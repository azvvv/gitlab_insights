"""
LDAP 认证服务
支持 Active Directory 和 OpenLDAP
"""

import logging
from typing import Optional, Dict, Tuple
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError
from config.ldap_config import LDAPConfig

logger = logging.getLogger(__name__)


class LDAPService:
    """LDAP 认证服务类"""
    
    def __init__(self):
        self.config = LDAPConfig
        self._validate_config()
    
    def _validate_config(self):
        """验证配置"""
        is_valid, error = self.config.validate_config()
        if not is_valid:
            logger.error(f"LDAP 配置无效: {error}")
            raise ValueError(f"LDAP 配置无效: {error}")
    
    def _get_server(self) -> Server:
        """创建 LDAP 服务器连接"""
        try:
            ldap_url = self.config.get_ldap_url()
            logger.debug(f"连接到 LDAP 服务器: {ldap_url}")
            
            server = Server(
                ldap_url,
                get_info=ALL,
                connect_timeout=self.config.LDAP_TIMEOUT
            )
            return server
        except Exception as e:
            logger.error(f"创建 LDAP 服务器连接失败: {str(e)}")
            raise
    
    def _search_user(self, username: str) -> Optional[str]:
        """
        搜索用户 DN
        
        Args:
            username: 用户名
            
        Returns:
            用户的 DN，如果未找到返回 None
        """
        try:
            server = self._get_server()
            
            # 使用绑定账户进行搜索
            conn = Connection(
                server,
                user=self.config.LDAP_BIND_DN,
                password=self.config.LDAP_BIND_PASSWORD,
                auto_bind=True
            )
            
            # 构建搜索过滤器
            search_filter = self.config.LDAP_USER_SEARCH_FILTER.format(username=username)
            logger.debug(f"LDAP 搜索过滤器: {search_filter}")
            
            # 执行搜索
            conn.search(
                search_base=self.config.LDAP_BASE_DN,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['*']
            )
            
            if len(conn.entries) == 0:
                logger.warning(f"未找到用户: {username}")
                return None
            
            if len(conn.entries) > 1:
                logger.warning(f"找到多个用户: {username}, 使用第一个")
            
            user_dn = conn.entries[0].entry_dn
            logger.debug(f"找到用户 DN: {user_dn}")
            
            conn.unbind()
            return user_dn
            
        except LDAPException as e:
            logger.error(f"LDAP 搜索失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"搜索用户时发生错误: {str(e)}")
            return None
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        LDAP 用户认证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (是否成功, 用户信息字典, 错误信息)
        """
        if not self.config.LDAP_ENABLED:
            return False, None, "LDAP 认证未启用"
        
        if not username or not password:
            return False, None, "用户名或密码为空"
        
        try:
            # 1. 搜索用户 DN
            user_dn = self._search_user(username)
            if not user_dn:
                return False, None, f"用户不存在: {username}"
            
            # 2. 尝试使用用户凭据绑定（认证）
            server = self._get_server()
            conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True
            )
            
            # 3. 认证成功，获取用户信息
            user_info = self._get_user_info(conn, user_dn)
            conn.unbind()
            
            logger.info(f"LDAP 认证成功: {username}")
            return True, user_info, None
            
        except LDAPBindError as e:
            logger.warning(f"LDAP 认证失败 (密码错误): {username}")
            return False, None, "用户名或密码错误"
        except LDAPException as e:
            logger.error(f"LDAP 认证异常: {str(e)}")
            return False, None, f"LDAP 服务器错误: {str(e)}"
        except Exception as e:
            logger.error(f"认证过程发生错误: {str(e)}")
            return False, None, f"认证失败: {str(e)}"
    
    def _get_user_info(self, conn: Connection, user_dn: str) -> Dict:
        """
        获取用户详细信息
        
        Args:
            conn: LDAP 连接对象
            user_dn: 用户 DN
            
        Returns:
            用户信息字典
        """
        try:
            # 重新搜索用户以获取所有属性
            conn.search(
                search_base=user_dn,
                search_filter='(objectClass=*)',
                search_scope=SUBTREE,
                attributes=['*']
            )
            
            if len(conn.entries) == 0:
                return {}
            
            entry = conn.entries[0]
            attr_map = self.config.LDAP_USER_ATTR_MAP
            
            # 提取用户信息
            user_info = {
                'dn': user_dn,
                'username': self._get_attr_value(entry, attr_map['username']),
                'email': self._get_attr_value(entry, attr_map['email']),
                'full_name': self._get_attr_value(entry, attr_map['full_name']),
                'first_name': self._get_attr_value(entry, attr_map.get('first_name', '')),
                'last_name': self._get_attr_value(entry, attr_map.get('last_name', '')),
            }
            
            # 检查是否为管理员
            if self.config.LDAP_ADMIN_GROUP:
                user_info['is_admin'] = self._check_admin_group(conn, user_dn)
            else:
                user_info['is_admin'] = False
            
            return user_info
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            return {'username': 'unknown'}
    
    def _get_attr_value(self, entry, attr_name: str) -> Optional[str]:
        """安全获取 LDAP 属性值"""
        if not attr_name:
            return None
        
        try:
            value = getattr(entry, attr_name, None)
            if value:
                return str(value.value) if hasattr(value, 'value') else str(value)
            return None
        except Exception:
            return None
    
    def _check_admin_group(self, conn: Connection, user_dn: str) -> bool:
        """
        检查用户是否属于管理员组
        
        Args:
            conn: LDAP 连接对象
            user_dn: 用户 DN
            
        Returns:
            是否为管理员
        """
        if not self.config.LDAP_ADMIN_GROUP:
            return False
        
        try:
            # 搜索组成员关系
            search_filter = self.config.LDAP_GROUP_SEARCH_FILTER.format(user_dn=user_dn)
            
            conn.search(
                search_base=self.config.LDAP_ADMIN_GROUP,
                search_filter=search_filter,
                search_scope=SUBTREE
            )
            
            return len(conn.entries) > 0
            
        except Exception as e:
            logger.error(f"检查管理员组失败: {str(e)}")
            return False
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        测试 LDAP 连接
        
        Returns:
            (是否成功, 错误信息)
        """
        if not self.config.LDAP_ENABLED:
            return False, "LDAP 未启用"
        
        try:
            server = self._get_server()
            
            # 尝试匿名绑定或使用绑定账户
            if self.config.LDAP_BIND_DN:
                conn = Connection(
                    server,
                    user=self.config.LDAP_BIND_DN,
                    password=self.config.LDAP_BIND_PASSWORD,
                    auto_bind=True
                )
            else:
                conn = Connection(server, auto_bind=True)
            
            # 测试搜索
            conn.search(
                search_base=self.config.LDAP_BASE_DN,
                search_filter='(objectClass=*)',
                search_scope=SUBTREE,
                size_limit=1
            )
            
            conn.unbind()
            logger.info("LDAP 连接测试成功")
            return True, None
            
        except LDAPBindError as e:
            error_msg = f"LDAP 绑定失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except LDAPException as e:
            error_msg = f"LDAP 连接失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_config_info(self) -> Dict:
        """获取 LDAP 配置信息（隐藏敏感信息）"""
        return {
            'enabled': self.config.LDAP_ENABLED,
            'host': self.config.LDAP_HOST,
            'port': self.config.LDAP_PORT,
            'use_ssl': self.config.LDAP_USE_SSL,
            'base_dn': self.config.LDAP_BASE_DN,
            'bind_dn': self.config.LDAP_BIND_DN if self.config.LDAP_BIND_DN else '(未配置)',
            'user_search_filter': self.config.LDAP_USER_SEARCH_FILTER,
            'auto_create_user': self.config.LDAP_AUTO_CREATE_USER,
            'sync_user_info': self.config.LDAP_SYNC_USER_INFO,
            'admin_group': self.config.LDAP_ADMIN_GROUP if self.config.LDAP_ADMIN_GROUP else '(未配置)',
        }
