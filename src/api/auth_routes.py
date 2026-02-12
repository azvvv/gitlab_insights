"""
认证相关 API 路由
提供用户登录、Token 验证、密码管理、LDAP 认证等功能
"""
from flask import Blueprint, request, g
from services.auth_service import AuthService
from api.response import api_response
from api.auth_decorators import token_required, admin_required
from utils.errorhandler import handle_exceptions

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
@handle_exceptions
def login():
    """用户登录"""
    if not request.is_json:
        return api_response(success=False, error='需要 JSON 格式数据', status_code=400)
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return api_response(success=False, error='用户名和密码不能为空', status_code=400)
    
    auth_service = AuthService()
    success, token, user_info, error = auth_service.login(username, password)
    
    if success:
        return api_response(
            success=True,
            message='登录成功',
            token=token,
            user=user_info
        )
    else:
        return api_response(
            success=False,
            error=error,
            status_code=401
        )


@auth_bp.route('/ldap-login', methods=['POST'])
@handle_exceptions
def ldap_login():
    """LDAP 用户登录"""
    if not request.is_json:
        return api_response(success=False, error='需要 JSON 格式数据', status_code=400)
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return api_response(success=False, error='用户名和密码不能为空', status_code=400)
    
    auth_service = AuthService()
    success, token, user_info, error = auth_service.login_with_ldap(username, password)
    
    if success:
        return api_response(
            success=True,
            message='LDAP 登录成功',
            token=token,
            user=user_info
        )
    else:
        return api_response(
            success=False,
            error=error,
            status_code=401
        )


@auth_bp.route('/auto-login', methods=['POST'])
@handle_exceptions
def auto_login():
    """
    自动登录 - 先尝试本地认证，失败后尝试 LDAP
    推荐前端使用此接口，可自动选择认证方式
    """
    if not request.is_json:
        return api_response(success=False, error='需要 JSON 格式数据', status_code=400)
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return api_response(success=False, error='用户名和密码不能为空', status_code=400)
    
    auth_service = AuthService()
    success, token, user_info, error = auth_service.login_auto(username, password)
    
    if success:
        auth_type = user_info.get('auth_type', 'local') if user_info else 'local'
        return api_response(
            success=True,
            message=f'登录成功 ({auth_type})',
            token=token,
            user=user_info
        )
    else:
        return api_response(
            success=False,
            error=error,
            status_code=401
        )


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token():
    """验证 Token 是否有效"""
    return api_response(
        success=True,
        message='Token 有效',
        user=g.current_user
    )


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """获取当前登录用户信息"""
    return api_response(
        success=True,
        user=g.current_user
    )


@auth_bp.route('/change-password', methods=['POST'])
@token_required
@handle_exceptions
def change_password():
    """修改密码"""
    if not request.is_json:
        return api_response(success=False, error='需要 JSON 格式数据', status_code=400)
    
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return api_response(success=False, error='旧密码和新密码不能为空', status_code=400)
    
    if len(new_password) < 6:
        return api_response(success=False, error='新密码长度至少6位', status_code=400)
    
    auth_service = AuthService()
    success, error = auth_service.change_password(
        g.current_user['user_id'],
        old_password,
        new_password
    )
    
    if success:
        return api_response(success=True, message='密码修改成功')
    else:
        return api_response(success=False, error=error, status_code=400)


@auth_bp.route('/ldap/test', methods=['GET'])
@token_required
@admin_required
@handle_exceptions
def test_ldap_connection():
    """测试 LDAP 连接（仅管理员）"""
    try:
        from services.ldap_service import LDAPService
        from config.ldap_config import LDAPConfig
        
        if not LDAPConfig.LDAP_ENABLED:
            return api_response(
                success=False,
                message='LDAP 未启用',
                config=LDAPService().get_config_info() if LDAPService else {}
            )
        
        ldap_service = LDAPService()
        success, error = ldap_service.test_connection()
        
        if success:
            return api_response(
                success=True,
                message='LDAP 连接测试成功',
                config=ldap_service.get_config_info()
            )
        else:
            return api_response(
                success=False,
                message='LDAP 连接测试失败',
                error=error,
                config=ldap_service.get_config_info(),
                status_code=500
            )
    except Exception as e:
        return api_response(
            success=False,
            error=f'LDAP 测试失败: {str(e)}',
            status_code=500
        )


@auth_bp.route('/ldap/config', methods=['GET'])
@token_required
@admin_required
def get_ldap_config():
    """获取 LDAP 配置信息（仅管理员，敏感信息已隐藏）"""
    try:
        from services.ldap_service import LDAPService
        ldap_service = LDAPService()
        return api_response(
            success=True,
            config=ldap_service.get_config_info()
        )
    except Exception as e:
        return api_response(
            success=False,
            error=f'获取配置失败: {str(e)}',
            status_code=500
        )
