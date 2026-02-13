"""
LDAP 认证服务 - 向后兼容桥接

实际实现已移至 shared.ldap_service，此处仅做重导出。
新代码请直接使用: from shared.ldap_service import LDAPService
"""
from shared.ldap_service import LDAPService

__all__ = ['LDAPService']

