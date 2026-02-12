"""
日志配置模块
提供统一的日志配置和管理功能
"""
import os
import logging
import logging.handlers
from pathlib import Path
from config.settings import settings


class LoggingConfig:
    """日志配置类"""
    
    # 日志级别映射
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(self):
        """初始化日志配置（使用统一配置管理）"""
        # 从统一配置读取
        log_config = settings.logging
        
        self.log_level = log_config.level
        self.log_format = log_config.format
        self.log_to_file = log_config.to_file
        self.log_to_console = log_config.to_console
        self.log_dir = log_config.dir
        self.log_file_max_bytes = log_config.file_max_bytes
        self.log_file_backup_count = log_config.file_backup_count
        self.log_json = log_config.json_format
        
        # 创建日志目录
        if self.log_to_file:
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)
    
    def get_log_level(self):
        """获取日志级别"""
        return self.LOG_LEVELS.get(self.log_level, logging.INFO)
    
    def get_formatter(self, for_file=False):
        """
        获取日志格式化器
        
        Args:
            for_file: 是否为文件日志（文件日志包含更多详细信息）
        
        Returns:
            logging.Formatter: 日志格式化器
        """
        if self.log_json:
            # JSON 格式（需要额外的库，这里提供简化版）
            return logging.Formatter(
                '{"time":"%(asctime)s", "level":"%(levelname)s", "name":"%(name)s", '
                '"file":"%(pathname)s", "line":%(lineno)d, "message":"%(message)s"}'
            )
        
        if self.log_format == 'detailed' or for_file:
            # 详细格式（用于文件）
            return logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            # 标准格式（用于控制台）
            return logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    
    def get_console_handler(self):
        """
        获取控制台处理器
        
        Returns:
            logging.Handler: 控制台处理器
        """
        if not self.log_to_console:
            return None
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.get_log_level())
        console_handler.setFormatter(self.get_formatter(for_file=False))
        return console_handler
    
    def get_file_handler(self, log_type='app'):
        """
        获取文件处理器（带日志轮转）
        
        Args:
            log_type: 日志类型（app, error, access 等）
        
        Returns:
            logging.Handler: 文件处理器
        """
        if not self.log_to_file:
            return None
        
        # 根据日志类型设置不同的文件名
        log_filename = os.path.join(self.log_dir, f'{log_type}.log')
        
        # 使用 TimedRotatingFileHandler 替代 RotatingFileHandler
        # 这在 Windows 多线程环境下更稳定，避免文件锁问题
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_filename,
            when='midnight',  # 每天午夜轮转
            interval=1,
            backupCount=self.log_file_backup_count,
            encoding='utf-8'
        )
        # 设置日志文件后缀格式
        file_handler.suffix = "%Y-%m-%d"
        
        # 文件日志使用更高的详细级别
        file_handler.setLevel(self.get_log_level())
        file_handler.setFormatter(self.get_formatter(for_file=True))
        
        return file_handler
    
    def get_error_file_handler(self):
        """
        获取错误日志文件处理器（只记录 ERROR 及以上级别）
        
        Returns:
            logging.Handler: 错误日志文件处理器
        """
        if not self.log_to_file:
            return None
        
        log_filename = os.path.join(self.log_dir, 'error.log')
        
        # 使用 TimedRotatingFileHandler 替代 RotatingFileHandler
        # 这在 Windows 多线程环境下更稳定，避免文件锁问题
        error_handler = logging.handlers.TimedRotatingFileHandler(
            log_filename,
            when='midnight',  # 每天午夜轮转
            interval=1,
            backupCount=self.log_file_backup_count,
            encoding='utf-8'
        )
        # 设置日志文件后缀格式
        error_handler.suffix = "%Y-%m-%d"
        
        # 只记录 ERROR 及以上级别
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.get_formatter(for_file=True))
        
        return error_handler
    
    def setup_logger(self, name, log_type='app'):
        """
        设置并返回一个配置好的日志记录器
        
        Args:
            name: 日志记录器名称（通常使用 __name__）
            log_type: 日志类型（用于文件名）
        
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        logger = logging.getLogger(name)
        
        # 如果已经配置过，直接返回
        if logger.handlers:
            return logger
        
        logger.setLevel(self.get_log_level())
        
        # 添加控制台处理器
        console_handler = self.get_console_handler()
        if console_handler:
            logger.addHandler(console_handler)
        
        # 添加文件处理器
        file_handler = self.get_file_handler(log_type)
        if file_handler:
            logger.addHandler(file_handler)
        
        # 添加错误日志处理器
        error_handler = self.get_error_file_handler()
        if error_handler:
            logger.addHandler(error_handler)
        
        # 防止日志向上传播到根日志记录器
        logger.propagate = False
        
        return logger
    
    def setup_root_logger(self):
        """
        设置根日志记录器
        用于捕获第三方库的日志
        """
        root_logger = logging.getLogger()
        
        # 清除现有的处理器
        root_logger.handlers.clear()
        
        root_logger.setLevel(self.get_log_level())
        
        # 添加控制台处理器
        console_handler = self.get_console_handler()
        if console_handler:
            root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        file_handler = self.get_file_handler('root')
        if file_handler:
            root_logger.addHandler(file_handler)
        
        return root_logger
    
    def get_config_info(self):
        """
        获取当前日志配置信息
        
        Returns:
            dict: 配置信息字典
        """
        return {
            'log_level': self.log_level,
            'log_format': self.log_format,
            'log_to_file': self.log_to_file,
            'log_to_console': self.log_to_console,
            'log_dir': self.log_dir,
            'log_file_max_bytes': self.log_file_max_bytes,
            'log_file_backup_count': self.log_file_backup_count,
            'log_json': self.log_json
        }


# 全局日志配置实例
_logging_config = None


def get_logging_config():
    """
    获取全局日志配置实例（单例模式）
    
    Returns:
        LoggingConfig: 日志配置实例
    """
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
    return _logging_config


def init_logging():
    """
    初始化日志系统
    在应用启动时调用
    """
    config = get_logging_config()
    config.setup_root_logger()
    
    # 记录初始化信息
    logger = config.setup_logger('logging_init')
    logger.info('日志系统初始化完成')
    logger.info(f'日志配置: {config.get_config_info()}')
