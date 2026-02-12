"""
API 响应工具
提供统一的 API 响应格式和处理函数
"""
from flask import jsonify
from typing import Any, Dict


def api_response(success: bool = True, data: Any = None, message: str = None, 
                error: str = None, status_code: int = 200, **kwargs) -> tuple:
    """
    统一的 API 响应格式
    
    Args:
        success: 操作是否成功
        data: 响应数据
        message: 成功消息
        error: 错误消息
        status_code: HTTP 状态码
        **kwargs: 其他自定义字段
    
    Returns:
        (Flask Response, status_code) 元组
    
    Example:
        >>> # 成功响应
        >>> return api_response(success=True, data={'users': users}, message='获取成功')
        
        >>> # 错误响应
        >>> return api_response(success=False, error='用户不存在', status_code=404)
        
        >>> # 自定义字段
        >>> return api_response(success=True, data=projects, total=100, page=1)
    """
    response = {
        'success': success,
    }
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
        
    if error:
        response['error'] = error
        response['success'] = False
    
    # 添加其他自定义字段
    response.update(kwargs)
    
    return jsonify(response), status_code


def handle_service_result(result: Any) -> Dict:
    """
    统一处理服务层返回的结果对象
    将对象转换为字典格式，便于 JSON 序列化
    
    Args:
        result: 服务层返回的结果对象（可能是对象、字典或其他类型）
    
    Returns:
        标准化的字典格式
    
    Example:
        >>> result = service.sync_repositories()
        >>> result_dict = handle_service_result(result)
        >>> return api_response(**result_dict)
    """
    if hasattr(result, '__dict__'):
        # 如果是对象，提取常见属性
        result_dict = {}
        
        # 常见的结果属性
        common_attrs = ['success', 'message', 'data', 'error', 'count', 'inserted', 'skipped']
        
        for attr in common_attrs:
            if hasattr(result, attr):
                result_dict[attr] = getattr(result, attr)
        
        # 如果没有找到任何属性，尝试转换整个对象
        if not result_dict:
            try:
                result_dict = result.__dict__
            except:
                result_dict = {'data': str(result)}
        
        # 确保有 success 字段
        if 'success' not in result_dict:
            result_dict['success'] = True
            
        return result_dict
    
    # 如果已经是字典，直接返回
    if isinstance(result, dict):
        return result
    
    # 其他情况，包装为标准格式
    return {'success': True, 'data': result}


def success_response(data: Any = None, message: str = None, **kwargs) -> tuple:
    """
    成功响应的快捷方法
    
    Args:
        data: 响应数据
        message: 成功消息
        **kwargs: 其他字段
    
    Returns:
        (Flask Response, 200)
    
    Example:
        >>> return success_response(data={'users': users}, message='获取成功')
    """
    return api_response(success=True, data=data, message=message, status_code=200, **kwargs)


def error_response(error: str, status_code: int = 400, **kwargs) -> tuple:
    """
    错误响应的快捷方法
    
    Args:
        error: 错误消息
        status_code: HTTP 状态码（默认 400）
        **kwargs: 其他字段
    
    Returns:
        (Flask Response, status_code)
    
    Example:
        >>> return error_response('用户不存在', status_code=404)
    """
    return api_response(success=False, error=error, status_code=status_code, **kwargs)


def created_response(data: Any = None, message: str = '创建成功', **kwargs) -> tuple:
    """
    创建成功响应（201）
    
    Args:
        data: 创建的资源数据
        message: 成功消息
        **kwargs: 其他字段
    
    Returns:
        (Flask Response, 201)
    """
    return api_response(success=True, data=data, message=message, status_code=201, **kwargs)


def no_content_response() -> tuple:
    """
    无内容响应（204）
    通常用于删除操作
    
    Returns:
        (Flask Response, 204)
    """
    return '', 204
