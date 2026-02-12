"""
日志中间件
记录所有 HTTP 请求和响应信息
"""
import time
import os
from flask import request, g
from functools import wraps
from utils.logger import access_logger, security_logger


def get_current_user_id():
    """
    从 Flask g 对象中安全地获取当前用户 ID
    
    Returns:
        用户 ID 或 None
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        return None
    
    # g.current_user 可能是字典（JWT payload）或对象（User model）
    if isinstance(g.current_user, dict):
        return g.current_user.get('id') or g.current_user.get('user_id')
    else:
        return getattr(g.current_user, 'id', None)


class LoggingMiddleware:
    """Flask 日志中间件"""
    
    # 慢请求阈值配置（毫秒）
    DEFAULT_SLOW_REQUEST_THRESHOLD = 1000  # 默认 1 秒
    
    # 长时间运行的路径模式及其自定义阈值（毫秒）
    LONG_RUNNING_PATHS = {
        '/api/gitlab/sync-repositories': 30000,    # 30秒
        '/api/gitlab/sync-groups': 30000,          # 30秒
        '/api/gitlab/sync-branches': 20000,        # 20秒
        '/api/gitlab/sync-permissions': 20000,     # 20秒
        '/api/gitlab/sync-all': 60000,             # 60秒
        '/api/parse-log': 10000,                   # 10秒
        '/api/branch-rules/apply': 15000,          # 15秒
        '/api/branches/deletion-report/excel': 10000,  # 10秒
    }
    
    def __init__(self, app=None):
        """
        初始化日志中间件
        
        Args:
            app: Flask 应用实例
        """
        from config.settings import settings
        
        self.app = app
        
        # 从统一配置读取默认阈值
        self.default_threshold = settings.app.slow_request_threshold
        
        if app is not None:
            self.init_app(app)
    
    def get_slow_threshold(self, path):
        """
        获取指定路径的慢请求阈值
        
        Args:
            path: 请求路径
        
        Returns:
            int: 慢请求阈值（毫秒）
        """
        # 精确匹配
        if path in self.LONG_RUNNING_PATHS:
            return self.LONG_RUNNING_PATHS[path]
        
        # 前缀匹配（例如 /api/gitlab/sync-*）
        for pattern, threshold in self.LONG_RUNNING_PATHS.items():
            if path.startswith(pattern.rstrip('*')):
                return threshold
        
        return self.default_threshold
    
    def init_app(self, app):
        """
        初始化中间件到 Flask 应用
        
        Args:
            app: Flask 应用实例
        """
        # 请求开始前
        app.before_request(self.before_request)
        
        # 请求结束后
        app.after_request(self.after_request)
        
        # 请求异常时
        app.teardown_request(self.teardown_request)
    
    @staticmethod
    def before_request():
        """请求开始前的处理"""
        # 记录请求开始时间
        g.request_start_time = time.time()
        
        # 记录请求信息（调试级别）
        access_logger.debug(
            f"收到请求: {request.method} {request.path} "
            f"from {request.remote_addr}"
        )
    
    def after_request(self, response):
        """
        请求结束后的处理
        
        Args:
            response: Flask 响应对象
        
        Returns:
            response: 原始响应对象
        """
        # 计算请求处理时间
        if hasattr(g, 'request_start_time'):
            elapsed_time = (time.time() - g.request_start_time) * 1000  # 转换为毫秒
        else:
            elapsed_time = 0
        
        # 获取用户信息
        user_id = get_current_user_id()
        
        # 获取请求信息
        method = request.method
        path = request.path
        status_code = response.status_code
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # 构建日志消息
        log_message = (
            f"{method} {path} - "
            f"Status: {status_code} - "
            f"Time: {elapsed_time:.2f}ms - "
            f"IP: {ip_address}"
        )
        
        if user_id:
            log_message += f" - User: {user_id}"
        
        # 根据状态码选择日志级别
        if status_code >= 500:
            access_logger.error(log_message)
        elif status_code >= 400:
            access_logger.warning(log_message)
        else:
            access_logger.info(log_message)
        
        # 记录慢请求（使用动态阈值）
        slow_threshold = self.get_slow_threshold(path)
        if elapsed_time > slow_threshold:
            access_logger.warning(
                f"慢请求: {method} {path} - {elapsed_time:.2f}ms "
                f"(阈值: {slow_threshold}ms)"
            )
        
        # 记录详细的请求信息（调试级别）
        access_logger.debug(
            f"请求详情: User-Agent: {user_agent}, "
            f"Content-Type: {request.content_type}"
        )
        
        return response
    
    @staticmethod
    def teardown_request(exception=None):
        """
        请求销毁时的处理（包括异常情况）
        
        Args:
            exception: 异常对象（如果有）
        """
        if exception:
            # 记录异常信息
            access_logger.error(
                f"请求处理异常: {request.method} {request.path} - "
                f"Exception: {str(exception)}",
                exc_info=True
            )


def log_request_body(max_length=1000):
    """
    记录请求体装饰器
    用于需要记录请求参数的 API 端点
    
    Args:
        max_length: 最大记录长度，避免日志过大
    
    Example:
        >>> @app.route('/api/data', methods=['POST'])
        >>> @log_request_body()
        >>> def create_data():
        >>>     return {"status": "success"}
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 记录请求参数
            if request.is_json:
                try:
                    body = str(request.get_json())
                    if len(body) > max_length:
                        body = body[:max_length] + '...'
                    access_logger.debug(f"请求体 (JSON): {body}")
                except Exception as e:
                    access_logger.warning(f"无法解析请求体: {str(e)}")
            elif request.form:
                body = str(dict(request.form))
                if len(body) > max_length:
                    body = body[:max_length] + '...'
                access_logger.debug(f"请求体 (Form): {body}")
            
            # 记录查询参数
            if request.args:
                access_logger.debug(f"查询参数: {dict(request.args)}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_response_body(max_length=1000):
    """
    记录响应体装饰器
    用于需要记录响应数据的 API 端点
    
    Args:
        max_length: 最大记录长度
    
    Example:
        >>> @app.route('/api/data', methods=['GET'])
        >>> @log_response_body()
        >>> def get_data():
        >>>     return {"status": "success", "data": [...]}
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            
            # 记录响应数据
            try:
                if hasattr(response, 'get_json'):
                    body = str(response.get_json())
                else:
                    body = str(response)
                
                if len(body) > max_length:
                    body = body[:max_length] + '...'
                
                access_logger.debug(f"响应体: {body}")
            except Exception as e:
                access_logger.warning(f"无法记录响应体: {str(e)}")
            
            return response
        return wrapper
    return decorator


def log_security_event_decorator(event_type):
    """
    安全事件日志装饰器
    用于记录安全相关的操作
    
    Args:
        event_type: 事件类型
    
    Example:
        >>> @app.route('/api/auth/login', methods=['POST'])
        >>> @log_security_event_decorator('login_attempt')
        >>> def login():
        >>>     # 登录逻辑
        >>>     pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = get_current_user_id()
            ip_address = request.remote_addr
            
            # 记录安全事件
            security_logger.info(
                f"[{event_type}] "
                f"IP: {ip_address} "
                f"{'User: ' + str(user_id) if user_id else 'Anonymous'} "
                f"Path: {request.path}"
            )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def skip_logging(func):
    """
    跳过日志记录装饰器
    用于不需要记录日志的端点（如健康检查）
    
    Example:
        >>> @app.route('/health')
        >>> @skip_logging
        >>> def health_check():
        >>>     return {"status": "healthy"}
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        g.skip_logging = True
        return func(*args, **kwargs)
    return wrapper
