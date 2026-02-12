"""
统一配置管理模块

提供应用所有配置的集中管理、类型安全和启动时验证。
所有配置通过环境变量加载，支持 .env 文件。

使用示例:
    from config.settings import settings
    
    # 访问配置
    db_url = settings.database.url
    gitlab_url = settings.gitlab.url
    debug_mode = settings.app.debug
"""

import os
import re
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ConfigurationError(Exception):
    """配置错误异常"""
    pass


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ConfigurationError(
                "DATABASE_URL 环境变量未设置。\n"
                "请在 .env 文件中配置: DATABASE_URL=postgresql://user:password@localhost:5432/gitlab_insight"
            )
        
        return cls(
            url=url,
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )


@dataclass
class GitLabConfig:
    """GitLab 配置"""
    url: str
    token: str
    timeout: int = 30
    verify_ssl: bool = True
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        url = os.getenv("GITLAB_URL")
        token = os.getenv("GITLAB_TOKEN")
        
        if not url:
            raise ConfigurationError(
                "GITLAB_URL 环境变量未设置。\n"
                "请在 .env 文件中配置: GITLAB_URL=https://gitlab.example.com"
            )
        if not token:
            raise ConfigurationError(
                "GITLAB_TOKEN 环境变量未设置。\n"
                "请在 .env 文件中配置: GITLAB_TOKEN=your_gitlab_personal_access_token"
            )
        
        return cls(
            url=url,
            token=token,
            timeout=int(os.getenv("GITLAB_TIMEOUT", "30")),
            verify_ssl=os.getenv("GITLAB_VERIFY_SSL", "true").lower() == "true"
        )


@dataclass
class JWTConfig:
    """JWT 认证配置"""
    secret_key: str
    expiry_hours: int = 24
    algorithm: str = "HS256"
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        secret_key = os.getenv("JWT_SECRET_KEY")
        env = os.getenv("FLASK_ENV", "development")
        
        # 生产环境必须设置强密钥
        if not secret_key or secret_key == "your-secret-key-change-in-production":
            if env == "production":
                raise ConfigurationError(
                    "生产环境必须设置强随机的 JWT_SECRET_KEY。\n"
                    "建议使用至少 32 个字符的随机字符串。"
                )
            # 开发环境使用默认密钥（带警告）
            secret_key = "dev-secret-key-not-for-production"
        
        return cls(
            secret_key=secret_key,
            expiry_hours=int(os.getenv("JWT_EXPIRY_HOURS", "24")),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256")
        )


@dataclass
class LDAPConfig:
    """LDAP 认证配置"""
    enabled: bool
    host: Optional[str] = None
    port: int = 389
    use_ssl: bool = False
    timeout: int = 10
    bind_dn: Optional[str] = None
    bind_password: Optional[str] = None
    base_dn: Optional[str] = None
    user_search_filter: str = "(uid={username})"
    auto_create_user: bool = True
    sync_user_info: bool = True
    admin_group: Optional[str] = None
    group_search_filter: str = "(member={user_dn})"
    
    # 用户属性映射
    attr_username: str = "uid"
    attr_email: str = "mail"
    attr_fullname: str = "cn"
    attr_firstname: str = "givenName"
    attr_lastname: str = "sn"
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        enabled = os.getenv("LDAP_ENABLED", "false").lower() == "true"
        
        config = cls(
            enabled=enabled,
            host=os.getenv("LDAP_HOST"),
            port=int(os.getenv("LDAP_PORT", "389")),
            use_ssl=os.getenv("LDAP_USE_SSL", "false").lower() == "true",
            timeout=int(os.getenv("LDAP_TIMEOUT", "10")),
            bind_dn=os.getenv("LDAP_BIND_DN"),
            bind_password=os.getenv("LDAP_BIND_PASSWORD"),
            base_dn=os.getenv("LDAP_BASE_DN"),
            user_search_filter=os.getenv("LDAP_USER_SEARCH_FILTER", "(uid={username})"),
            auto_create_user=os.getenv("LDAP_AUTO_CREATE_USER", "true").lower() == "true",
            sync_user_info=os.getenv("LDAP_SYNC_USER_INFO", "true").lower() == "true",
            admin_group=os.getenv("LDAP_ADMIN_GROUP"),
            group_search_filter=os.getenv("LDAP_GROUP_SEARCH_FILTER", "(member={user_dn})"),
            attr_username=os.getenv("LDAP_ATTR_USERNAME", "uid"),
            attr_email=os.getenv("LDAP_ATTR_EMAIL", "mail"),
            attr_fullname=os.getenv("LDAP_ATTR_FULLNAME", "cn"),
            attr_firstname=os.getenv("LDAP_ATTR_FIRSTNAME", "givenName"),
            attr_lastname=os.getenv("LDAP_ATTR_LASTNAME", "sn")
        )
        
        # 如果启用了 LDAP，验证必需配置
        if enabled:
            if not config.host:
                raise ConfigurationError(
                    "LDAP_HOST 未设置但 LDAP 已启用。\n"
                    "请在 .env 文件中配置: LDAP_HOST=ldap://ldap.example.com"
                )
            if not config.base_dn:
                raise ConfigurationError(
                    "LDAP_BASE_DN 未设置但 LDAP 已启用。\n"
                    "请在 .env 文件中配置: LDAP_BASE_DN=dc=example,dc=com"
                )
        
        return config
    
    @property
    def user_attr_map(self) -> dict:
        """返回用户属性映射字典（向后兼容）"""
        return {
            'username': self.attr_username,
            'email': self.attr_email,
            'full_name': self.attr_fullname,
            'first_name': self.attr_firstname,
            'last_name': self.attr_lastname,
        }


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "standard"
    to_file: bool = True
    to_console: bool = True
    dir: str = "logs"
    file_max_bytes: int = 10 * 1024 * 1024  # 10MB
    file_backup_count: int = 5
    json_format: bool = False
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO").upper(),
            format=os.getenv("LOG_FORMAT", "standard"),
            to_file=os.getenv("LOG_TO_FILE", "true").lower() == "true",
            to_console=os.getenv("LOG_TO_CONSOLE", "true").lower() == "true",
            dir=os.getenv("LOG_DIR", "logs"),
            file_max_bytes=int(os.getenv("LOG_FILE_MAX_BYTES", str(10 * 1024 * 1024))),
            file_backup_count=int(os.getenv("LOG_FILE_BACKUP_COUNT", "5")),
            json_format=os.getenv("LOG_JSON", "false").lower() == "true"
        )


@dataclass
class AppConfig:
    """应用配置"""
    port: int = 5000
    host: str = "0.0.0.0"
    debug: bool = False
    init_db: bool = False
    environment: str = "development"
    log_file_path: Optional[str] = None
    slow_request_threshold: int = 1000  # 毫秒
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            port=int(os.getenv("API_PORT", "5000")),
            host=os.getenv("API_HOST", "0.0.0.0"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            init_db=os.getenv("INIT_DB", "false").lower() == "true",
            environment=os.getenv("FLASK_ENV", "development"),
            log_file_path=os.getenv("LOG_FILE_PATH"),
            slow_request_threshold=int(os.getenv("SLOW_REQUEST_THRESHOLD", "1000"))
        )


@dataclass
class TaskConfig:
    """异步任务配置"""
    min_interval: int = 300  # 5 分钟
    max_concurrent: int = 10
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            min_interval=int(os.getenv("TASK_MIN_INTERVAL", "300")),
            max_concurrent=int(os.getenv("MAX_CONCURRENT_TASKS", "10"))
        )


class Settings:
    """
    应用全局配置
    
    使用示例:
        from config.settings import settings
        
        # 访问配置
        print(settings.database.url)
        print(settings.gitlab.url)
        print(settings.app.debug)
    """
    
    def __init__(self):
        """初始化所有配置并验证"""
        self._load_all_configs()
        self._validate_all_configs()
    
    def _load_all_configs(self):
        """加载所有配置"""
        try:
            self.app = AppConfig.from_env()
            self.database = DatabaseConfig.from_env()
            self.gitlab = GitLabConfig.from_env()
            self.jwt = JWTConfig.from_env()
            self.ldap = LDAPConfig.from_env()
            self.logging = LoggingConfig.from_env()
            self.task = TaskConfig.from_env()
        except ConfigurationError:
            # 重新抛出配置错误，不包装
            raise
        except Exception as e:
            raise ConfigurationError(f"配置加载失败: {str(e)}")
    
    def _validate_all_configs(self):
        """验证所有配置"""
        errors = []
        
        # 验证端口范围
        if not (1 <= self.app.port <= 65535):
            errors.append(f"API_PORT 必须在 1-65535 之间，当前值: {self.app.port}")
        
        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level not in valid_log_levels:
            errors.append(
                f"LOG_LEVEL 必须是 {valid_log_levels} 之一，当前值: {self.logging.level}"
            )
        
        # 验证日志格式
        valid_log_formats = ["standard", "detailed"]
        if self.logging.format not in valid_log_formats:
            errors.append(
                f"LOG_FORMAT 必须是 {valid_log_formats} 之一，当前值: {self.logging.format}"
            )
        
        # 生产环境检查
        if self.app.environment == "production":
            if self.app.debug:
                errors.append("生产环境不应启用 DEBUG 模式")
            
            # 检查数据库 URL 是否包含默认密码
            if any(pwd in self.database.url.lower() for pwd in ["password@", "password:", "123456", "admin"]):
                errors.append("生产环境请修改数据库默认密码")
            
            # 检查 JWT 密钥强度
            if len(self.jwt.secret_key) < 32:
                errors.append("生产环境 JWT_SECRET_KEY 应至少 32 个字符")
        
        if errors:
            raise ConfigurationError(
                "配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors)
            )
    
    def reload(self):
        """重新加载配置（用于测试或动态更新）"""
        load_dotenv(override=True)
        self._load_all_configs()
        self._validate_all_configs()
    
    def to_dict(self, mask_sensitive: bool = True) -> dict:
        """
        转换为字典（用于日志记录）
        
        Args:
            mask_sensitive: 是否隐藏敏感信息（密码、token等）
        
        Returns:
            配置字典
        """
        return {
            "app": {
                "port": self.app.port,
                "host": self.app.host,
                "debug": self.app.debug,
                "environment": self.app.environment,
                "init_db": self.app.init_db,
                "slow_request_threshold": self.app.slow_request_threshold
            },
            "database": {
                "url": self._mask_password(self.database.url) if mask_sensitive else self.database.url,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow,
                "echo": self.database.echo
            },
            "gitlab": {
                "url": self.gitlab.url,
                "token": "***" if mask_sensitive and self.gitlab.token else self.gitlab.token,
                "timeout": self.gitlab.timeout,
                "verify_ssl": self.gitlab.verify_ssl
            },
            "jwt": {
                "secret_key": "***" if mask_sensitive else self.jwt.secret_key,
                "expiry_hours": self.jwt.expiry_hours,
                "algorithm": self.jwt.algorithm
            },
            "ldap": {
                "enabled": self.ldap.enabled,
                "host": self.ldap.host,
                "port": self.ldap.port,
                "use_ssl": self.ldap.use_ssl,
                "base_dn": self.ldap.base_dn,
                "bind_dn": self.ldap.bind_dn,
                "bind_password": "***" if mask_sensitive and self.ldap.bind_password else self.ldap.bind_password,
                "auto_create_user": self.ldap.auto_create_user
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "to_file": self.logging.to_file,
                "to_console": self.logging.to_console,
                "dir": self.logging.dir,
                "json_format": self.logging.json_format
            },
            "task": {
                "min_interval": self.task.min_interval,
                "max_concurrent": self.task.max_concurrent
            }
        }
    
    @staticmethod
    def _mask_password(url: str) -> str:
        """隐藏 URL 中的密码"""
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', url)


# 全局单例配置对象
# 在模块导入时自动加载和验证配置
settings: Settings = None

try:
    settings = Settings()
except ConfigurationError as e:
    # 配置错误时，打印错误信息但不中断导入
    # 这样可以在某些情况下（如生成文档）导入模块而不需要完整配置
    import sys
    print(f"警告: 配置加载失败: {e}", file=sys.stderr)
    print("如果您正在运行应用，请检查 .env 文件配置", file=sys.stderr)
    # 重新抛出异常，让应用决定如何处理
    raise
