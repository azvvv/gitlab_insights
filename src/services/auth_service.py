"""
认证服务 - 处理用户登录业务逻辑
支持本地用户和 LDAP 用户认证

重构说明：
- Token 生成和验证已移至 shared.auth_middleware
- 本服务专注于登录业务逻辑和用户管理
"""
from datetime import datetime
from typing import Optional, Dict, Tuple
from database.models import User
from database.connection import get_db_session
from utils.logger import get_logger, log_security_event
from config.settings import settings

# 导入 shared 模块
import sys
import os
if os.path.dirname(os.path.dirname(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared.auth_middleware import generate_token, verify_token

logger = get_logger(__name__, 'security')

class AuthService:
    """认证服务类 - 专注于用户登录和管理业务逻辑"""
    
    def __init__(self):
        # LDAP 服务（延迟加载）
        self._ldap_service = None
    
    @property
    def ldap_service(self):
        """延迟加载 LDAP 服务"""
        if self._ldap_service is None:
            try:
                from services.ldap_service import LDAPService
                
                if settings.ldap.enabled:
                    self._ldap_service = LDAPService()
                    logger.info("LDAP 服务已启用")
                else:
                    logger.info("LDAP 服务未启用")
            except Exception as e:
                logger.warning(f"LDAP 服务初始化失败: {str(e)}")
                self._ldap_service = None
        
        return self._ldap_service
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict], Optional[str]]:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (success, token, user_info, error_message)
        """
        logger.info(f"用户登录尝试: username={username}")
        
        try:
            with get_db_session() as session:
                # 查找用户
                user = session.query(User).filter(User.username == username).first()
                
                if not user:
                    logger.warning(f"登录失败 - 用户不存在: username={username}")
                    log_security_event('login_failed', user_id=None, details=f'用户不存在: {username}')
                    return False, None, None, '用户不存在'
                
                if not user.is_active:
                    logger.warning(f"登录失败 - 用户已被禁用: user_id={user.id}")
                    log_security_event('login_failed', user_id=user.id, details='用户已被禁用')
                    return False, None, None, '用户已被禁用'
                
                # 验证密码
                if not user.check_password(password):
                    logger.warning(f"登录失败 - 密码错误: user_id={user.id}")
                    log_security_event('login_failed', user_id=user.id, details='密码错误')
                    return False, None, None, '密码错误'
                
                # 更新最后登录时间
                user.last_login = datetime.now()
                session.commit()
                
                # 使用 shared 模块生成 token
                token = generate_token(user.id, user.username, user.is_admin)
                
                # 返回用户信息（不包含密码）
                user_info = user.to_dict()
                
                logger.info(f"用户登录成功: user_id={user.id}, username={username}")
                log_security_event('login_success', user_id=user.id, details='本地用户登录成功')
                
                return True, token, user_info, None
                
        except Exception as e:
            logger.error(f"登录异常: username={username}, error={str(e)}", exc_info=True)
            log_security_event('login_error', user_id=None, details=f'登录异常: {str(e)}')
            return False, None, None, f'登录失败: {str(e)}'
    
    def login_with_ldap(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict], Optional[str]]:
        """
        LDAP 用户登录
        
        Args:
            username: 用户名（LDAP 用户名）
            password: 密码
            
        Returns:
            (success, token, user_info, error_message)
        """
        # 检查 LDAP 是否启用
        if not self.ldap_service:
            return False, None, None, 'LDAP 认证未启用'
        
        try:
            # 1. LDAP 认证
            success, ldap_user_info, error = self.ldap_service.authenticate(username, password)
            
            if not success:
                return False, None, None, error or 'LDAP 认证失败'
            
            # 2. 在本地数据库中查找或创建用户
            # 使用邮箱作为唯一标识，避免因用户名格式不同而重复创建
            with get_db_session() as session:
                from config.ldap_config import LDAPConfig
                
                # 优先使用邮箱查找用户（避免重复）
                ldap_email = ldap_user_info.get('email')
                user = None
                
                if ldap_email:
                    # 先通过邮箱查找
                    user = session.query(User).filter(User.email == ldap_email).first()
                    logger.debug(f"通过邮箱 {ldap_email} 查找用户: {'找到' if user else '未找到'}")
                
                if not user:
                    # 如果通过邮箱没找到，再尝试用户名
                    user = session.query(User).filter(User.username == username).first()
                    logger.debug(f"通过用户名 {username} 查找用户: {'找到' if user else '未找到'}")
                
                # 如果用户不存在且允许自动创建
                if not user and LDAPConfig.LDAP_AUTO_CREATE_USER:
                    # 使用 LDAP 返回的规范用户名（通常是 cn）
                    canonical_username = ldap_user_info.get('username', username)
                    logger.info(f"自动创建 LDAP 用户: {canonical_username} (邮箱: {ldap_email})")
                    
                    user = User(
                        username=canonical_username,  # 使用 LDAP 的规范用户名
                        email=ldap_email,
                        full_name=ldap_user_info.get('full_name'),
                        is_admin=ldap_user_info.get('is_admin', False),
                        is_active=True
                    )
                    # LDAP 用户不需要本地密码，设置一个随机密码
                    import secrets
                    user.set_password(secrets.token_urlsafe(32))
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                
                elif not user:
                    return False, None, None, f'用户 {username} 未在本地数据库中注册'
                
                # 如果用户存在，更新用户信息（如果启用同步）
                elif LDAPConfig.LDAP_SYNC_USER_INFO:
                    if ldap_user_info.get('email'):
                        user.email = ldap_user_info['email']
                    if ldap_user_info.get('full_name'):
                        user.full_name = ldap_user_info['full_name']
                    if 'is_admin' in ldap_user_info:
                        user.is_admin = ldap_user_info['is_admin']
                    session.commit()
                
                # 检查用户是否激活
                if not user.is_active:
                    return False, None, None, '用户已被禁用'
                
                # 更新最后登录时间
                user.last_login = datetime.now()
                session.commit()
                
                # 使用 shared 模块生成 token
                token = generate_token(user.id, user.username, user.is_admin)
                
                # 返回用户信息
                user_info = user.to_dict()
                user_info['auth_type'] = 'ldap'
                
                logger.info(f"LDAP 用户登录成功: {username}")
                return True, token, user_info, None
                
        except Exception as e:
            logger.error(f"LDAP 登录失败: {str(e)}")
            return False, None, None, f'LDAP 登录失败: {str(e)}'
    
    def login_auto(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict], Optional[str]]:
        """
        自动选择认证方式：先尝试本地认证，失败后尝试 LDAP
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (success, token, user_info, error_message)
        """
        # 1. 先尝试本地认证
        success, token, user_info, error = self.login(username, password)
        
        if success:
            if user_info:
                user_info['auth_type'] = 'local'
            return True, token, user_info, None
        
        # 2. 如果本地认证失败且 LDAP 已启用，尝试 LDAP 认证
        if self.ldap_service:
            logger.info(f"本地认证失败，尝试 LDAP 认证: {username}")
            return self.login_with_ldap(username, password)
        
        # 3. 都失败了
        return False, None, None, error
    
    # generate_token 和 verify_token 已移至 shared.auth_middleware
    # 如需使用，请导入：from shared.auth_middleware import generate_token, verify_token
    
    def create_user(self, username: str, password: str, email: Optional[str] = None, 
                   full_name: Optional[str] = None, is_admin: bool = False) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        创建新用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            full_name: 全名
            is_admin: 是否管理员
            
        Returns:
            (success, user, error_message)
        """
        try:
            with get_db_session() as session:
                # 检查用户名是否已存在
                existing_user = session.query(User).filter(User.username == username).first()
                if existing_user:
                    return False, None, '用户名已存在'
                
                # 创建新用户
                user = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    is_admin=is_admin,
                    is_active=True
                )
                user.set_password(password)
                
                session.add(user)
                session.commit()
                session.refresh(user)
                
                return True, user, None
                
        except Exception as e:
            return False, None, f'创建用户失败: {str(e)}'
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            (success, error_message)
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return False, '用户不存在'
                
                # 验证旧密码
                if not user.check_password(old_password):
                    return False, '旧密码错误'
                
                # 设置新密码
                user.set_password(new_password)
                session.commit()
                
                return True, None
                
        except Exception as e:
            return False, f'修改密码失败: {str(e)}'
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            User 对象或 None
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    # 创建一个独立的对象以避免 session 关闭后访问问题
                    session.expunge(user)
                return user
        except Exception:
            return None
