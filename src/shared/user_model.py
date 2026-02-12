"""
共享用户服务 - 多应用用户管理
========================================

功能：
1. 用户查询（按 ID、用户名）
2. 用户创建和更新
3. 权限验证
4. 跨应用用户数据共享

使用场景：
- 在模型评估应用中获取用户信息
- 跨应用的权限验证
- 用户状态检查
"""
import sys
import os

# 确保可以导入数据库模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.models import User
from database.connection import get_db_session
from typing import Optional, List
from datetime import datetime

class SharedUserService:
    """
    共享用户服务
    
    提供跨应用的用户管理功能
    """
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """
        根据 ID 获取用户
        
        Args:
            user_id: 用户 ID
            
        Returns:
            User 对象，如果不存在返回 None
            
        Example:
            >>> user = SharedUserService.get_user_by_id(1)
            >>> if user:
            >>>     print(f"用户名: {user.username}")
        """
        with get_db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                # 刷新对象，确保在 session 外也能访问属性
                session.refresh(user)
            return user
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            User 对象，如果不存在返回 None
            
        Example:
            >>> user = SharedUserService.get_user_by_username('admin')
            >>> if user:
            >>>     print(f"用户 ID: {user.id}")
        """
        with get_db_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                session.refresh(user)
            return user
    
    @staticmethod
    def get_user_info(user_id: int) -> Optional[dict]:
        """
        获取用户信息（字典格式）
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户信息字典，如果不存在返回 None
            
        Example:
            >>> info = SharedUserService.get_user_info(1)
            >>> print(info['username'])
        """
        user = SharedUserService.get_user_by_id(user_id)
        if user:
            return user.to_dict()
        return None
    
    @staticmethod
    def is_user_active(user_id: int) -> bool:
        """
        检查用户是否激活
        
        Args:
            user_id: 用户 ID
            
        Returns:
            True 如果用户存在且激活，否则 False
        """
        user = SharedUserService.get_user_by_id(user_id)
        return user is not None and user.is_active
    
    @staticmethod
    def is_user_admin(user_id: int) -> bool:
        """
        检查用户是否为管理员
        
        Args:
            user_id: 用户 ID
            
        Returns:
            True 如果用户是管理员，否则 False
        """
        user = SharedUserService.get_user_by_id(user_id)
        return user is not None and user.is_admin
    
    @staticmethod
    def update_last_login(user_id: int):
        """
        更新用户最后登录时间
        
        Args:
            user_id: 用户 ID
        """
        with get_db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login = datetime.now()
                session.commit()
    
    @staticmethod
    def get_all_users(include_inactive: bool = False) -> List[dict]:
        """
        获取所有用户
        
        Args:
            include_inactive: 是否包含未激活的用户
            
        Returns:
            用户信息列表
        """
        with get_db_session() as session:
            query = session.query(User)
            
            if not include_inactive:
                query = query.filter(User.is_active == True)
            
            users = query.all()
            return [user.to_dict() for user in users]
    
    @staticmethod
    def verify_password(username: str, password: str) -> tuple[bool, Optional[User]]:
        """
        验证用户密码
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (验证是否成功, User 对象)
            
        Example:
            >>> success, user = SharedUserService.verify_password('admin', 'password123')
            >>> if success:
            >>>     print(f"登录成功: {user.username}")
        """
        user = SharedUserService.get_user_by_username(username)
        
        if not user:
            return False, None
        
        if not user.is_active:
            return False, None
        
        if user.check_password(password):
            return True, user
        
        return False, None

# ==================== 权限相关（如果使用权限系统）====================

class SharedPermissionService:
    """
    共享权限服务
    
    如果你实现了权限系统，可以在这里添加权限检查方法
    """
    
    @staticmethod
    def has_permission(user_id: int, permission_name: str) -> bool:
        """
        检查用户是否有特定权限
        
        Args:
            user_id: 用户 ID
            permission_name: 权限名称（如 'model:read', 'model:write'）
            
        Returns:
            True 如果有权限，否则 False
            
        Example:
            >>> if SharedPermissionService.has_permission(1, 'model:evaluate'):
            >>>     # 允许评估模型
        """
        # TODO: 实现权限检查逻辑
        # 这里需要根据你的权限系统实现
        
        # 示例实现：管理员拥有所有权限
        user = SharedUserService.get_user_by_id(user_id)
        if user and user.is_admin:
            return True
        
        # 其他用户的权限检查
        # 如果你有 Permission 模型，可以这样检查：
        # with get_db_session() as session:
        #     user = session.query(User).filter(User.id == user_id).first()
        #     if user:
        #         return any(p.name == permission_name for p in user.permissions)
        
        return False
    
    @staticmethod
    def has_app_access(user_id: int, app_name: str) -> bool:
        """
        检查用户是否能访问特定应用
        
        Args:
            user_id: 用户 ID
            app_name: 应用名称（如 'gitlab', 'model'）
            
        Returns:
            True 如果有访问权限，否则 False
        """
        # TODO: 实现应用访问权限检查
        
        # 示例实现：默认所有激活用户都能访问
        return SharedUserService.is_user_active(user_id)

# ==================== 使用示例 ====================

"""
使用示例:

# 在模型评估应用中使用
from shared.user_model import SharedUserService, SharedPermissionService

# 获取用户信息
user = SharedUserService.get_user_by_id(1)
if user:
    print(f"用户名: {user.username}")
    print(f"是否管理员: {user.is_admin}")

# 检查用户状态
if SharedUserService.is_user_active(1):
    print("用户已激活")

# 验证密码
success, user = SharedUserService.verify_password('admin', 'password')
if success:
    print("密码验证成功")

# 检查权限
if SharedPermissionService.has_permission(1, 'model:evaluate'):
    print("用户有评估权限")

# 检查应用访问权限
if SharedPermissionService.has_app_access(1, 'model'):
    print("用户可以访问模型评估应用")
"""
