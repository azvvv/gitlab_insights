"""
认证服务 - 向后兼容桥接

实际实现已移至 shared.auth_service，此处仅做重导出。
新代码请直接使用: from shared.auth_service import AuthService
"""
from shared.auth_service import AuthService

__all__ = ['AuthService']

