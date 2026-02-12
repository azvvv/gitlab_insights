"""
共享认证中间件 - 支持多应用集成
============================================

功能：
1. JWT Token 生成和验证
2. 通用认证装饰器
3. 支持多个 Flask 应用共享认证

使用场景：
- GitLab Insight 主应用
- 模型评估应用
- 未来的其他集成应用
"""
from functools import wraps
from flask import request, g
import jwt
from datetime import datetime, timedelta
import os

class SharedAuthConfig:
    """
    共享认证配置
    
    优先级：环境变量 > settings 配置 > 默认值
    这样可以兼容 GitLab Insight 的 settings 和外部应用的环境变量
    """
    _secret_key = None
    _algorithm = None
    _token_expiry_hours = None
    
    @classmethod
    def get_secret_key(cls):
        """获取 JWT 密钥（优先环境变量，回退到 settings）"""
        if cls._secret_key is None:
            # 优先从环境变量读取
            cls._secret_key = os.getenv('JWT_SECRET_KEY')
            
            # 如果环境变量没有，尝试从 settings 读取
            if not cls._secret_key:
                try:
                    from config.settings import settings
                    cls._secret_key = settings.jwt.secret_key
                except (ImportError, AttributeError):
                    # 如果 settings 也没有，使用默认值（仅用于开发）
                    cls._secret_key = 'your-secret-key-change-in-production'
        
        return cls._secret_key
    
    @classmethod
    def get_algorithm(cls):
        """获取 JWT 算法"""
        if cls._algorithm is None:
            cls._algorithm = os.getenv('JWT_ALGORITHM')
            
            if not cls._algorithm:
                try:
                    from config.settings import settings
                    cls._algorithm = settings.jwt.algorithm
                except (ImportError, AttributeError):
                    cls._algorithm = 'HS256'
        
        return cls._algorithm
    
    @classmethod
    def get_token_expiry_hours(cls):
        """获取 Token 过期时间（小时）"""
        if cls._token_expiry_hours is None:
            expiry_str = os.getenv('JWT_EXPIRY_HOURS')
            
            if expiry_str:
                cls._token_expiry_hours = int(expiry_str)
            else:
                try:
                    from config.settings import settings
                    cls._token_expiry_hours = settings.jwt.expiry_hours
                except (ImportError, AttributeError):
                    cls._token_expiry_hours = 24
        
        return cls._token_expiry_hours

def generate_token(user_id: int, username: str, is_admin: bool = False, 
                   extra_claims: dict = None) -> str:
    """
    生成 JWT Token
    
    Args:
        user_id: 用户 ID
        username: 用户名
        is_admin: 是否为管理员
        extra_claims: 额外的声明数据（如权限列表）
    
    Returns:
        JWT Token 字符串
    
    Example:
        >>> token = generate_token(1, 'admin', True, {'permissions': ['model:read']})
    """
    expiry = datetime.utcnow() + timedelta(hours=SharedAuthConfig.get_token_expiry_hours())
    
    payload = {
        'user_id': user_id,
        'username': username,
        'is_admin': is_admin,
        'exp': expiry,
        'iat': datetime.utcnow()
    }
    
    # 添加额外声明
    if extra_claims:
        payload.update(extra_claims)
    
    token = jwt.encode(
        payload,
        SharedAuthConfig.get_secret_key(),
        algorithm=SharedAuthConfig.get_algorithm()
    )
    
    return token

def verify_token(token: str):
    """
    验证 JWT Token
    
    Args:
        token: JWT Token 字符串
    
    Returns:
        (success: bool, payload: dict, error: str)
        
    Example:
        >>> success, payload, error = verify_token(token)
        >>> if success:
        >>>     user_id = payload['user_id']
    """
    try:
        payload = jwt.decode(
            token, 
            SharedAuthConfig.get_secret_key(), 
            algorithms=[SharedAuthConfig.get_algorithm()]
        )
        return True, payload, None
        
    except jwt.ExpiredSignatureError:
        return False, None, 'Token 已过期，请重新登录'
        
    except jwt.InvalidTokenError as e:
        return False, None, f'Token 无效: {str(e)}'

def token_required(response_formatter=None):
    """
    通用 Token 认证装饰器
    
    支持自定义响应格式，适配不同应用的需求
    
    使用方法:
        # 方式 1: 默认字典格式（新应用）
        @app.route('/api/protected', methods=['GET'])
        @token_required()
        def protected_route():
            return {'message': 'Success'}
        
        # 方式 2: 自定义响应格式（GitLab Insight）
        from api.response import api_response
        
        @app.route('/api/protected', methods=['GET'])
        @token_required(response_formatter=api_response)
        def protected_route():
            return api_response(message='Success')
        
        # 方式 3: 直接作为装饰器（向后兼容）
        @app.route('/api/protected', methods=['GET'])
        @token_required
        def protected_route():
            return {'message': 'Success'}
    
    Args:
        response_formatter: 可选的响应格式化函数
                          接收 (success, error, status_code) 参数
                          返回格式化的响应
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # 从 Authorization header 获取 token
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                try:
                    # 解析 Bearer token 格式
                    parts = auth_header.split(' ')
                    if len(parts) == 2 and parts[0] == 'Bearer':
                        token = parts[1]
                    else:
                        error_msg = 'Token 格式错误，应为: Bearer <token>'
                        if response_formatter:
                            return response_formatter(success=False, error=error_msg, status_code=401)
                        return {'success': False, 'error': error_msg}, 401
                except (IndexError, AttributeError):
                    error_msg = 'Token 格式错误'
                    if response_formatter:
                        return response_formatter(success=False, error=error_msg, status_code=401)
                    return {'success': False, 'error': error_msg}, 401
            
            if not token:
                error_msg = '缺少认证 token，请在 Authorization Header 中提供'
                if response_formatter:
                    return response_formatter(success=False, error=error_msg, status_code=401)
                return {'success': False, 'error': error_msg}, 401
            
            # 验证 token
            success, payload, error = verify_token(token)
            
            if not success:
                if response_formatter:
                    return response_formatter(success=False, error=error or 'Token 验证失败', status_code=401)
                return {'success': False, 'error': error}, 401
            
            # 将用户信息存储到 Flask 的 g 对象中
            g.current_user = payload
            
            return f(*args, **kwargs)
        
        return decorated
    
    # 支持不带括号的使用方式（向后兼容）
    # @token_required  而不是 @token_required()
    if callable(response_formatter):
        # response_formatter 实际上是被装饰的函数
        func = response_formatter
        response_formatter = None
        return decorator(func)
    
    return decorator

def admin_required(response_formatter=None):
    """
    管理员权限装饰器
    
    必须与 @token_required 一起使用，且放在 @token_required 之后
    支持自定义响应格式
    
    使用方法:
        # 方式 1: 默认格式
        @app.route('/api/admin-only', methods=['GET'])
        @token_required()
        @admin_required()
        def admin_route():
            return {'message': 'Admin access'}
        
        # 方式 2: 自定义格式
        @app.route('/api/admin-only', methods=['GET'])
        @token_required(response_formatter=api_response)
        @admin_required(response_formatter=api_response)
        def admin_route():
            return api_response(message='Admin access')
        
        # 方式 3: 向后兼容
        @app.route('/api/admin-only', methods=['GET'])
        @token_required
        @admin_required
        def admin_route():
            return {'message': 'Admin access'}
    
    注意:
        - 必须先使用 @token_required 进行认证
        - 只有 is_admin=True 的用户才能访问
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 检查是否已经通过 token_required 认证
            if not hasattr(g, 'current_user'):
                error_msg = '未认证，请先登录'
                if response_formatter:
                    return response_formatter(success=False, error=error_msg, status_code=401)
                return {'success': False, 'error': error_msg}, 401
            
            # 检查是否为管理员
            if not g.current_user.get('is_admin', False):
                error_msg = '需要管理员权限才能访问此资源'
                if response_formatter:
                    return response_formatter(success=False, error=error_msg, status_code=403)
                return {'success': False, 'error': error_msg}, 403
            
            return f(*args, **kwargs)
        
        return decorated
    
    # 支持不带括号的使用方式（向后兼容）
    if callable(response_formatter):
        func = response_formatter
        response_formatter = None
        return decorator(func)
    
    return decorator

def optional_token(f):
    """
    可选 Token 认证装饰器
    
    如果提供了 Token 则验证，如果没有提供则继续执行
    适用于既支持匿名访问又支持认证访问的接口
    
    使用方法:
        @app.route('/api/public-or-private', methods=['GET'])
        @optional_token
        def flexible_route():
            if hasattr(g, 'current_user'):
                # 已登录用户
                return {'message': f'Hello {g.current_user["username"]}'}
            else:
                # 匿名用户
                return {'message': 'Hello guest'}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 尝试从 Authorization header 获取 token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                pass  # 忽略格式错误，继续执行
        
        if token:
            # 如果有 token，尝试验证
            success, payload, error = verify_token(token)
            if success:
                g.current_user = payload
        
        # 无论是否有 token，都继续执行
        return f(*args, **kwargs)
    
    return decorated

# ==================== 工具函数 ====================

def get_current_user_id() -> int:
    """
    获取当前用户 ID
    
    Returns:
        用户 ID，如果未认证返回 None
        
    Example:
        @app.route('/api/my-data', methods=['GET'])
        @token_required
        def get_my_data():
            user_id = get_current_user_id()
            return {'user_id': user_id}
    """
    if hasattr(g, 'current_user'):
        return g.current_user.get('user_id')
    return None

def get_current_username() -> str:
    """获取当前用户名"""
    if hasattr(g, 'current_user'):
        return g.current_user.get('username')
    return None

def is_current_user_admin() -> bool:
    """判断当前用户是否为管理员"""
    if hasattr(g, 'current_user'):
        return g.current_user.get('is_admin', False)
    return False

# ==================== 使用示例 ====================

"""
完整使用示例:

# app.py
from flask import Flask
from shared.auth_middleware import token_required, admin_required, generate_token

app = Flask(__name__)

# 登录接口（生成 token）
@app.route('/api/login', methods=['POST'])
def login():
    # 验证用户名密码...
    token = generate_token(
        user_id=1, 
        username='admin', 
        is_admin=True,
        extra_claims={'permissions': ['read', 'write']}
    )
    return {'token': token}

# 需要登录的接口
@app.route('/api/protected', methods=['GET'])
@token_required
def protected():
    from flask import g
    return {'message': f'Hello {g.current_user["username"]}'}

# 需要管理员权限的接口
@app.route('/api/admin', methods=['GET'])
@token_required
@admin_required
def admin_only():
    return {'message': 'Admin access'}

if __name__ == '__main__':
    app.run()
"""
