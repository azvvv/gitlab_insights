"""
首页链接配置 API 路由
提供首页内容的增删改查和管理功能
"""
from flask import Blueprint, request
from services.home_link_service import HomeLinkService
from dto.home_link_dto import HomeLinkCreate, HomeLinkUpdate
from api.response import api_response
from api.auth_decorators import token_required, admin_required
from utils.errorhandler import handle_exceptions

home_link_bp = Blueprint('home_links', __name__)


@home_link_bp.route('', methods=['GET'])
@handle_exceptions
def get_home_links():
    """获取所有首页链接（公开接口，无需认证）
    
    Query Parameters:
        include_inactive (str): 如果为 'true'，则包含未激活的记录（用于管理页面）
    """
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        service = HomeLinkService()
        result = service.get_all_links(include_inactive=include_inactive)
        return api_response(
            success=True,
            data=result.dict()
        )
    except Exception as e:
        return api_response(
            success=False,
            error=f'获取首页链接失败: {str(e)}',
            status_code=500
        )


@home_link_bp.route('/category/<string:category>', methods=['GET'])
@handle_exceptions
def get_home_links_by_category(category):
    """按分类获取首页链接"""
    try:
        service = HomeLinkService()
        links = service.get_links_by_category(category)
        return api_response(
            success=True,
            data=[link.dict() for link in links]
        )
    except Exception as e:
        return api_response(
            success=False,
            error=f'获取链接失败: {str(e)}',
            status_code=500
        )


@home_link_bp.route('/category/<string:category>/group/<string:group_name>', methods=['GET'])
@handle_exceptions
def get_home_links_by_group(category, group_name):
    """按分类和分组获取首页链接"""
    try:
        service = HomeLinkService()
        links = service.get_links_by_group(category, group_name)
        return api_response(
            success=True,
            data=[link.dict() for link in links]
        )
    except Exception as e:
        return api_response(
            success=False,
            error=f'获取链接失败: {str(e)}',
            status_code=500
        )


@home_link_bp.route('/<int:link_id>', methods=['GET'])
@token_required
@handle_exceptions
def get_home_link(link_id):
    """根据ID获取链接（需要认证）"""
    try:
        service = HomeLinkService()
        link = service.get_link_by_id(link_id)
        if link:
            return api_response(
                success=True,
                data=link.dict()
            )
        else:
            return api_response(
                success=False,
                error='链接不存在',
                status_code=404
            )
    except Exception as e:
        return api_response(
            success=False,
            error=f'获取链接失败: {str(e)}',
            status_code=500
        )


@home_link_bp.route('', methods=['POST'])
@token_required
@admin_required
@handle_exceptions
def create_home_link():
    """创建新链接（需要管理员权限）"""
    if not request.is_json:
        return api_response(success=False, error='需要 JSON 格式数据', status_code=400)
    
    try:
        data = request.get_json()
        link_data = HomeLinkCreate(**data)
        
        service = HomeLinkService()
        new_link = service.create_link(link_data)
        return api_response(
            success=True,
            data=new_link.dict(),
            message='链接创建成功'
        )
    except Exception as e:
        return api_response(
            success=False,
            error=f'创建链接失败: {str(e)}',
            status_code=500
        )


@home_link_bp.route('/<int:link_id>', methods=['PUT'])
@token_required
@admin_required
@handle_exceptions
def update_home_link(link_id):
    """更新链接（需要管理员权限）"""
    if not request.is_json:
        return api_response(success=False, error='需要 JSON 格式数据', status_code=400)
    
    try:
        data = request.get_json()
        link_data = HomeLinkUpdate(**data)
        
        service = HomeLinkService()
        updated_link = service.update_link(link_id, link_data)
        
        if updated_link:
            return api_response(
                success=True,
                data=updated_link.dict(),
                message='链接更新成功'
            )
        else:
            return api_response(
                success=False,
                error='链接不存在',
                status_code=404
            )
    except Exception as e:
        return api_response(
            success=False,
            error=f'更新链接失败: {str(e)}',
            status_code=500
        )


@home_link_bp.route('/<int:link_id>', methods=['DELETE'])
@token_required
@admin_required
@handle_exceptions
def delete_home_link(link_id):
    """删除链接（需要管理员权限）"""
    try:
        service = HomeLinkService()
        success = service.delete_link(link_id)
        
        if success:
            return api_response(
                success=True,
                message='链接删除成功'
            )
        else:
            return api_response(
                success=False,
                error='链接不存在',
                status_code=404
            )
    except Exception as e:
        return api_response(
            success=False,
            error=f'删除链接失败: {str(e)}',
            status_code=500
        )


@home_link_bp.route('/<int:link_id>/toggle', methods=['POST'])
@token_required
@admin_required
@handle_exceptions
def toggle_home_link(link_id):
    """切换链接启用状态（需要管理员权限）"""
    try:
        service = HomeLinkService()
        updated_link = service.toggle_active(link_id)
        
        if updated_link:
            return api_response(
                success=True,
                data=updated_link.dict(),
                message='链接状态已更新'
            )
        else:
            return api_response(
                success=False,
                error='链接不存在',
                status_code=404
            )
    except Exception as e:
        return api_response(
            success=False,
            error=f'更新链接状态失败: {str(e)}',
            status_code=500
        )


@home_link_bp.route('/sort', methods=['PUT'])
@token_required
@admin_required
@handle_exceptions
def update_home_link_sort():
    """批量更新链接排序（需要管理员权限）"""
    if not request.is_json:
        return api_response(success=False, error='需要 JSON 格式数据', status_code=400)
    
    try:
        data = request.get_json()
        link_orders = data.get('orders', [])
        
        if not link_orders:
            return api_response(
                success=False,
                error='排序数据不能为空',
                status_code=400
            )
        
        service = HomeLinkService()
        success = service.update_sort_orders(link_orders)
        
        if success:
            return api_response(
                success=True,
                message='排序更新成功'
            )
        else:
            return api_response(
                success=False,
                error='排序更新失败',
                status_code=500
            )
    except Exception as e:
        return api_response(
            success=False,
            error=f'更新排序失败: {str(e)}',
            status_code=500
        )
