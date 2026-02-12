"""
数据验证工具
用于验证和处理 API 请求参数
"""
from functools import wraps
from flask import request
from typing import Any, Dict, List, Callable


def validate_json_request(required_fields: List[str] = None) -> Callable:
    """
    JSON 请求验证装饰器
    验证请求是否为 JSON 格式，并检查必需字段是否存在
    
    Args:
        required_fields: 必需字段列表
    
    Returns:
        装饰器函数
    
    Example:
        >>> @app.route('/api/users', methods=['POST'])
        >>> @validate_json_request(required_fields=['username', 'email'])
        >>> def create_user(validated_data):
        >>>     # validated_data 包含验证后的 JSON 数据
        >>>     username = validated_data['username']
        >>>     return {"success": True}
    
    Raises:
        返回 400 错误响应如果：
        - Content-Type 不是 application/json
        - 请求体为空
        - 缺少必需字段
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 导入放在这里避免循环依赖
            from api.response import api_response
            
            if not request.is_json:
                return api_response(
                    success=False,
                    error='Content-Type must be application/json',
                    status_code=400
                )
            
            data = request.get_json()
            if not data:
                return api_response(
                    success=False,
                    error='No JSON data provided',
                    status_code=400
                )
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return api_response(
                        success=False,
                        error=f'Missing required fields: {", ".join(missing_fields)}',
                        status_code=400
                    )
            
            # 将验证后的数据添加到 kwargs 中
            kwargs['validated_data'] = data
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_request_params(param_definitions: Dict[str, Dict]) -> Dict:
    """
    统一获取和验证请求参数
    支持 GET 查询参数和 POST JSON 参数
    
    Args:
        param_definitions: 参数定义字典，格式：
            {
                'param_name': {
                    'type': int,           # 参数类型
                    'default': None,       # 默认值
                    'required': False      # 是否必需
                }
            }
    
    Returns:
        验证后的参数字典
    
    Example:
        >>> param_defs = {
        >>>     'limit': {'type': int, 'default': 100},
        >>>     'offset': {'type': int, 'default': 0},
        >>>     'repository_id': {'type': int, 'required': True}
        >>> }
        >>> params = get_request_params(param_defs)
        >>> # {'limit': 100, 'offset': 0, 'repository_id': 123}
    
    Raises:
        ValueError: 如果必需参数缺失或类型转换失败
    """
    params = {}
    
    for param_name, definition in param_definitions.items():
        param_type = definition.get('type', str)
        default_value = definition.get('default')
        required = definition.get('required', False)
        
        if request.method == 'GET':
            # GET 请求从查询参数获取
            value = request.args.get(param_name, default_value, type=param_type)
        else:
            # POST/PUT/PATCH 请求从 JSON 获取
            data = request.get_json() if request.is_json else {}
            value = data.get(param_name, default_value)
            
            # 类型转换
            if value is not None and param_type != str:
                try:
                    value = param_type(value)
                except (ValueError, TypeError):
                    raise ValueError(f'Invalid type for parameter {param_name}')
        
        # 检查必需参数
        if required and value is None:
            raise ValueError(f'Required parameter {param_name} is missing')
        
        params[param_name] = value
    
    return params


def validate_param_type(value: Any, param_type: type, param_name: str) -> Any:
    """
    验证并转换参数类型
    
    Args:
        value: 参数值
        param_type: 期望的类型
        param_name: 参数名称（用于错误消息）
    
    Returns:
        转换后的值
    
    Raises:
        ValueError: 如果类型转换失败
    """
    if value is None:
        return None
    
    try:
        if param_type == bool:
            # 特殊处理布尔值
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        elif param_type == list:
            # 特殊处理列表
            if isinstance(value, str):
                return [item.strip() for item in value.split(',')]
            return list(value)
        else:
            return param_type(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f'Invalid type for parameter {param_name}: {str(e)}')


def validate_email(email: str) -> bool:
    """
    简单的邮箱格式验证
    
    Args:
        email: 邮箱地址
    
    Returns:
        是否为有效邮箱格式
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    简单的 URL 格式验证
    
    Args:
        url: URL 地址
    
    Returns:
        是否为有效 URL 格式
    """
    import re
    pattern = r'^https?://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})+(?:/.*)?$'
    return bool(re.match(pattern, url))
