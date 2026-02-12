"""
LDAP 认证配置
支持多种 LDAP 服务器：Active Directory, OpenLDAP 等

注意：此文件保持向后兼容，但建议使用 settings.ldap 访问配置
"""

from typing import Optional


class _LDAPConfigProxy:
    """LDAP 配置代理类（向后兼容）"""
    
    def __init__(self):
        self._settings = None
    
    def _get_settings(self):
        """延迟加载配置对象（避免循环导入）"""
        if self._settings is None:
            from config.settings import settings
            self._settings = settings.ldap
        return self._settings
    
    @property
    def LDAP_ENABLED(self) -> bool:
        return self._get_settings().enabled
    
    @property
    def LDAP_HOST(self) -> Optional[str]:
        return self._get_settings().host
    
    @property
    def LDAP_PORT(self) -> int:
        return self._get_settings().port
    
    @property
    def LDAP_USE_SSL(self) -> bool:
        return self._get_settings().use_ssl
    
    @property
    def LDAP_TIMEOUT(self) -> int:
        return self._get_settings().timeout
    
    @property
    def LDAP_BIND_DN(self) -> Optional[str]:
        return self._get_settings().bind_dn
    
    @property
    def LDAP_BIND_PASSWORD(self) -> Optional[str]:
        return self._get_settings().bind_password
    
    @property
    def LDAP_BASE_DN(self) -> Optional[str]:
        return self._get_settings().base_dn
    
    @property
    def LDAP_USER_SEARCH_FILTER(self) -> str:
        return self._get_settings().user_search_filter
    
    @property
    def LDAP_USER_ATTR_MAP(self) -> dict:
        return self._get_settings().user_attr_map
    
    @property
    def LDAP_ADMIN_GROUP(self) -> Optional[str]:
        return self._get_settings().admin_group
    
    @property
    def LDAP_GROUP_SEARCH_FILTER(self) -> str:
        return self._get_settings().group_search_filter
    
    @property
    def LDAP_AUTO_CREATE_USER(self) -> bool:
        return self._get_settings().auto_create_user
    
    @property
    def LDAP_SYNC_USER_INFO(self) -> bool:
        return self._get_settings().sync_user_info
    
    def get_ldap_url(self) -> str:
        """获取完整的 LDAP URL"""
        ldap = self._get_settings()
        protocol = 'ldaps' if ldap.use_ssl else 'ldap'
        host = ldap.host.replace('ldap://', '').replace('ldaps://', '') if ldap.host else 'localhost'
        return f"{protocol}://{host}:{ldap.port}"
    
    def is_configured(self) -> bool:
        """检查 LDAP 是否已正确配置"""
        ldap = self._get_settings()
        if not ldap.enabled:
            return False
        
        return bool(ldap.host and ldap.base_dn)
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """
        验证 LDAP 配置
        返回: (是否有效, 错误信息)
        """
        ldap = self._get_settings()
        
        if not ldap.enabled:
            return True, None
        
        if not ldap.host:
            return False, "LDAP_HOST 未配置"
        
        if not ldap.base_dn:
            return False, "LDAP_BASE_DN 未配置"
        
        if not ldap.user_search_filter:
            return False, "LDAP_USER_SEARCH_FILTER 未配置"
        
        if '{username}' not in ldap.user_search_filter:
            return False, "LDAP_USER_SEARCH_FILTER 必须包含 {username} 占位符"
        
        return True, None


# 创建单例实例
LDAPConfig = _LDAPConfigProxy()


# 预设配置模板
LDAP_CONFIG_TEMPLATES = {
    'active_directory': {
        'LDAP_PORT': '389',
        'LDAP_USER_SEARCH_FILTER': '(sAMAccountName={username})',
        'LDAP_ATTR_USERNAME': 'sAMAccountName',
        'LDAP_ATTR_EMAIL': 'mail',
        'LDAP_ATTR_FULLNAME': 'displayName',
        'LDAP_ATTR_FIRSTNAME': 'givenName',
        'LDAP_ATTR_LASTNAME': 'sn',
        'description': 'Microsoft Active Directory'
    },
    'openldap': {
        'LDAP_PORT': '389',
        'LDAP_USER_SEARCH_FILTER': '(uid={username})',
        'LDAP_ATTR_USERNAME': 'uid',
        'LDAP_ATTR_EMAIL': 'mail',
        'LDAP_ATTR_FULLNAME': 'cn',
        'LDAP_ATTR_FIRSTNAME': 'givenName',
        'LDAP_ATTR_LASTNAME': 'sn',
        'description': 'OpenLDAP'
    },
    'openldap_email': {
        'LDAP_PORT': '389',
        'LDAP_USER_SEARCH_FILTER': '(mail={username})',
        'LDAP_ATTR_USERNAME': 'mail',
        'LDAP_ATTR_EMAIL': 'mail',
        'LDAP_ATTR_FULLNAME': 'cn',
        'description': 'OpenLDAP (使用邮箱登录)'
    }
}
