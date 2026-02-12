"""
共享模块初始化
"""

from .auth_middleware import (
    token_required,
    admin_required,
    optional_token,
    generate_token,
    verify_token,
    get_current_user_id,
    get_current_username,
    is_current_user_admin
)

from .user_model import (
    SharedUserService,
    SharedPermissionService
)

__all__ = [
    # 认证装饰器
    'token_required',
    'admin_required',
    'optional_token',
    
    # Token 工具
    'generate_token',
    'verify_token',
    
    # 用户信息工具
    'get_current_user_id',
    'get_current_username',
    'is_current_user_admin',
    
    # 服务类
    'SharedUserService',
    'SharedPermissionService',
]
