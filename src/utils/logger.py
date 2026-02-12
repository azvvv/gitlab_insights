"""
日志工具模块
提供统一的日志获取接口
"""
import logging
from functools import wraps
from config.logging_config import get_logging_config


def get_logger(name=None, log_type='app'):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，通常传入 __name__
        log_type: 日志类型，用于区分不同的日志文件
                 - 'app': 应用日志（默认）
                 - 'access': 访问日志
                 - 'security': 安全日志
                 - 'gitlab': GitLab 操作日志
    
    Returns:
        logging.Logger: 配置好的日志记录器
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
        >>> logger.error("这是一条错误日志", exc_info=True)
    """
    config = get_logging_config()
    logger_name = name or 'app'
    return config.setup_logger(logger_name, log_type)


def log_execution(logger=None, log_args=False, log_result=False):
    """
    函数执行日志装饰器
    自动记录函数的执行、参数和结果
    
    Args:
        logger: 日志记录器，如果为 None 则自动创建
        log_args: 是否记录函数参数
        log_result: 是否记录函数返回值
    
    Example:
        >>> @log_execution(log_args=True, log_result=True)
        >>> def my_function(a, b):
        >>>     return a + b
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            # 记录函数开始执行
            if log_args:
                logger.debug(f"执行函数 {func_name}, args={args}, kwargs={kwargs}")
            else:
                logger.debug(f"执行函数 {func_name}")
            
            try:
                result = func(*args, **kwargs)
                
                # 记录函数执行成功
                if log_result:
                    logger.debug(f"函数 {func_name} 执行成功, result={result}")
                else:
                    logger.debug(f"函数 {func_name} 执行成功")
                
                return result
            except Exception as e:
                # 记录函数执行失败
                logger.error(f"函数 {func_name} 执行失败: {str(e)}", exc_info=True)
                raise
        
        return wrapper
    return decorator


def log_exception(logger=None, message=None, re_raise=True):
    """
    异常日志装饰器
    自动捕获并记录函数抛出的异常
    
    Args:
        logger: 日志记录器，如果为 None 则自动创建
        message: 自定义错误消息
        re_raise: 是否重新抛出异常
    
    Example:
        >>> @log_exception(message="处理数据时出错")
        >>> def process_data(data):
        >>>     # 处理数据
        >>>     pass
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = message or f"函数 {func.__name__} 发生异常"
                logger.error(f"{error_msg}: {str(e)}", exc_info=True)
                
                if re_raise:
                    raise
                return None
        
        return wrapper
    return decorator


class LoggerContext:
    """
    日志上下文管理器
    用于在特定代码块中添加额外的日志上下文信息
    
    Example:
        >>> with LoggerContext(logger, user_id=123, action="login"):
        >>>     logger.info("用户登录")
    """
    def __init__(self, logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        # 保存旧的记录工厂
        self.old_factory = logging.getLogRecordFactory()
        
        # 创建新的记录工厂，添加上下文信息
        context = self.context
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复旧的记录工厂
        logging.setLogRecordFactory(self.old_factory)


def log_performance(logger=None, threshold_ms=1000):
    """
    性能日志装饰器
    记录函数执行时间，如果超过阈值则发出警告
    
    Args:
        logger: 日志记录器
        threshold_ms: 时间阈值（毫秒），超过此值将记录警告
    
    Example:
        >>> @log_performance(threshold_ms=500)
        >>> def slow_function():
        >>>     time.sleep(1)
    """
    import time
    
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
                
                if elapsed_time > threshold_ms:
                    logger.warning(
                        f"函数 {func.__name__} 执行时间过长: {elapsed_time:.2f}ms "
                        f"(阈值: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"函数 {func.__name__} 执行时间: {elapsed_time:.2f}ms")
        
        return wrapper
    return decorator


# 预定义的日志记录器
app_logger = get_logger('app', 'app')
access_logger = get_logger('access', 'access')
security_logger = get_logger('security', 'security')
gitlab_logger = get_logger('gitlab', 'gitlab')


# 便捷函数
def log_info(message, logger_name='app'):
    """记录信息日志"""
    logger = get_logger(logger_name)
    logger.info(message)


def log_error(message, logger_name='app', exc_info=False):
    """记录错误日志"""
    logger = get_logger(logger_name)
    logger.error(message, exc_info=exc_info)


def log_warning(message, logger_name='app'):
    """记录警告日志"""
    logger = get_logger(logger_name)
    logger.warning(message)


def log_debug(message, logger_name='app'):
    """记录调试日志"""
    logger = get_logger(logger_name)
    logger.debug(message)


def log_access(method, path, status_code, response_time_ms, user_id=None):
    """
    记录 API 访问日志
    
    Args:
        method: HTTP 方法
        path: 请求路径
        status_code: 响应状态码
        response_time_ms: 响应时间（毫秒）
        user_id: 用户 ID（可选）
    """
    user_info = f"user_id={user_id}" if user_id else "anonymous"
    access_logger.info(
        f"{method} {path} - {status_code} - {response_time_ms:.2f}ms - {user_info}"
    )


def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """
    记录安全事件
    
    Args:
        event_type: 事件类型（如 login_success, login_failed, unauthorized_access）
        user_id: 用户 ID
        ip_address: IP 地址
        details: 详细信息
    """
    message = f"[{event_type}]"
    if user_id:
        message += f" user_id={user_id}"
    if ip_address:
        message += f" ip={ip_address}"
    if details:
        message += f" details={details}"
    
    security_logger.info(message)


def log_gitlab_operation(operation, project_id=None, user_id=None, details=None, success=True):
    """
    记录 GitLab 操作日志
    
    Args:
        operation: 操作类型（如 sync_projects, create_tag, delete_branch）
        project_id: 项目 ID
        user_id: 用户 ID
        details: 详细信息
        success: 是否成功
    """
    status = "SUCCESS" if success else "FAILED"
    message = f"[{operation}] [{status}]"
    
    if project_id:
        message += f" project_id={project_id}"
    if user_id:
        message += f" user_id={user_id}"
    if details:
        message += f" details={details}"
    
    if success:
        gitlab_logger.info(message)
    else:
        gitlab_logger.error(message)
