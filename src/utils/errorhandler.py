"""
错误处理工具
提供统一的错误处理和响应生成功能
"""
from typing import Dict, Any, Tuple, Optional, Callable
from flask import jsonify
from functools import wraps
from utils.logger import get_logger

logger = get_logger(__name__)


class APIErrorHandler:
    """
    统一的 API 错误处理器
    根据错误类型自动确定 HTTP 状态码和错误响应
    """

    # 错误类型到 HTTP 状态码的映射
    ERROR_STATUS_MAP = {
        # 认证相关 (401)
        'unauthorized': 401,
        'authentication': 401,
        'token': 401,
        '401': 401,

        # 权限相关 (403)
        'forbidden': 403,
        'permission': 403,
        '403': 403,

        # 资源不存在 (404)
        'not found': 404,
        'not exist': 404,
        '数据库未找到': 404,
        '404': 404,

        # 请求错误 (400)
        'bad request': 400,
        'invalid': 400,
        'validation': 400,
        'required': 400,
        '不在支持的': 400,
        '400': 400,

        # 服务器错误 (500)
        'internal': 500,
        'server': 500,
        'database': 500,
        'connection': 500,
        '500': 500,
    }

    @classmethod
    def determine_status_code(cls, error_message: str) -> int:
        """
        根据错误消息确定 HTTP 状态码

        Args:
            error_message: 错误消息字符串

        Returns:
            HTTP 状态码
        """
        if not error_message:
            return 500

        error_lower = error_message.lower()

        # 按优先级检查错误类型（优先级从高到低）
        priority_order = [
            ('401', 401), ('unauthorized', 401), ('token', 401), ('authentication', 401),
            ('403', 403), ('forbidden', 403), ('permission', 403),
            ('404', 404), ('not found', 404), ('not exist', 404), ('数据库未找到', 404),
            ('400', 400), ('bad request', 400), ('invalid', 400), ('validation', 400),
            ('required', 400), ('不在支持的', 400),
            ('500', 500), ('internal', 500), ('server', 500), ('database', 500), ('connection', 500),
        ]

        for error_type, status_code in priority_order:
            if error_type in error_lower:
                return status_code

        # 默认返回 500
        return 500

    @classmethod
    def create_error_response(cls, error: Exception = None, error_message: str = None,
                            status_code: int = None, **kwargs) -> Tuple[Dict[str, Any], int]:
        """
        创建统一的错误响应

        Args:
            error: 异常对象
            error_message: 错误消息
            status_code: 指定的 HTTP 状态码，如果不指定则自动确定
            **kwargs: 额外的响应数据

        Returns:
            (response_dict, status_code) 元组
        """
        # 获取错误消息
        if error_message is None and error:
            error_message = str(error)
        elif error_message is None:
            error_message = "Unknown error occurred"

        # 确定状态码
        if status_code is None:
            status_code = cls.determine_status_code(error_message)

        # 记录错误日志
        if error:
            logger.error(f"API 错误: {error_message}", exc_info=True)
        else:
            logger.error(f"API 错误: {error_message}")

        # 创建响应
        response = {
            'success': False,
            'error': error_message,
            **kwargs
        }

        return response, status_code

    @classmethod
    def create_success_response(cls, data: Any = None, message: str = None,
                              status_code: int = 200, **kwargs) -> Tuple[Dict[str, Any], int]:
        """
        创建统一的成功响应

        Args:
            data: 响应数据
            message: 成功消息
            status_code: HTTP 状态码
            **kwargs: 额外的响应数据

        Returns:
            (response_dict, status_code) 元组
        """
        response = {
            'success': True,
            **kwargs
        }

        if data is not None:
            response['data'] = data
        if message:
            response['message'] = message

        return response, status_code

    @classmethod
    def handle_service_response(cls, service_result: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        处理服务层返回的结果，确定合适的 HTTP 状态码

        Args:
            service_result: 服务层返回的字典结果

        Returns:
            (response_dict, status_code) 元组
        """
        if service_result.get('success', True):
            return service_result, 200

        # 处理失败情况
        error_message = service_result.get('error', 'Unknown error')
        status_code = cls.determine_status_code(error_message)

        # 记录错误
        logger.error(f"服务层错误: {error_message}")

        return service_result, status_code

    @classmethod
    def jsonify_response(cls, response_data: Dict[str, Any], status_code: int) -> Tuple[Any, int]:
        """
        将响应数据转换为 Flask jsonify 响应

        Args:
            response_data: 响应字典
            status_code: HTTP 状态码

        Returns:
            Flask jsonify 响应和状态码
        """
        return jsonify(response_data), status_code


class APIResponse:
    """
    API 响应工厂类
    提供便捷的方法创建各种类型的响应
    """

    @staticmethod
    def success(data: Any = None, message: str = None, **kwargs) -> Tuple[Any, int]:
        """创建成功响应"""
        response, status = APIErrorHandler.create_success_response(data, message, **kwargs)
        return APIErrorHandler.jsonify_response(response, status)

    @staticmethod
    def error(error: Exception = None, error_message: str = None,
              status_code: int = None, **kwargs) -> Tuple[Any, int]:
        """创建错误响应"""
        response, status = APIErrorHandler.create_error_response(error, error_message, status_code, **kwargs)
        return APIErrorHandler.jsonify_response(response, status)

    @staticmethod
    def bad_request(message: str = "Bad request", **kwargs) -> Tuple[Any, int]:
        """创建 400 错误响应"""
        return APIResponse.error(error_message=message, status_code=400, **kwargs)

    @staticmethod
    def unauthorized(message: str = "Unauthorized", **kwargs) -> Tuple[Any, int]:
        """创建 401 错误响应"""
        return APIResponse.error(error_message=message, status_code=401, **kwargs)

    @staticmethod
    def forbidden(message: str = "Forbidden", **kwargs) -> Tuple[Any, int]:
        """创建 403 错误响应"""
        return APIResponse.error(error_message=message, status_code=403, **kwargs)

    @staticmethod
    def not_found(message: str = "Not found", **kwargs) -> Tuple[Any, int]:
        """创建 404 错误响应"""
        return APIResponse.error(error_message=message, status_code=404, **kwargs)

    @staticmethod
    def internal_error(message: str = "Internal server error", **kwargs) -> Tuple[Any, int]:
        """创建 500 错误响应"""
        return APIResponse.error(error_message=message, status_code=500, **kwargs)


def smart_handle_exceptions(f: Callable) -> Callable:
    """
    智能异常处理装饰器
    根据异常类型自动确定 HTTP 状态码
    
    Example:
        >>> @app.route('/api/users')
        >>> @smart_handle_exceptions
        >>> def get_users():
        >>>     return service.get_users()
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)

            # 如果返回的是字典结果（服务层响应），智能处理
            if isinstance(result, dict):
                return APIErrorHandler.handle_service_response(result)

            # 如果返回的是元组（response, status_code），直接返回
            if isinstance(result, tuple) and len(result) == 2:
                return result

            # 其他情况直接返回
            return result

        except Exception as e:
            logger.error(f"函数 {f.__name__} 发生异常", exc_info=True)
            return APIErrorHandler.create_error_response(error=e)

    return decorated_function


def handle_exceptions(f: Callable) -> Callable:
    """
    统一异常处理装饰器
    捕获所有异常并返回 500 错误响应
    
    Example:
        >>> @app.route('/api/data')
        >>> @handle_exceptions
        >>> def get_data():
        >>>     # 如果抛出异常，自动返回错误响应
        >>>     return process_data()
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"函数 {f.__name__} 发生异常: {str(e)}", exc_info=True)
            # 导入放在这里避免循环依赖
            from api.response import api_response
            return api_response(
                success=False,
                error=str(e),
                status_code=500
            )
    return decorated_function
