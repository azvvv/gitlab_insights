"""
任务管理 API

包含以下功能：
- 获取任务状态
- 查询任务列表
- 取消任务
"""

from flask import Blueprint
from services.task_service import task_service, TaskStatus
from api.response import api_response
from api.auth_decorators import token_required
from utils.validators import get_request_params
from utils.errorhandler import handle_exceptions

task_bp = Blueprint('task', __name__)


@task_bp.route('/<task_id>', methods=['GET'])
@token_required
@handle_exceptions
def get_task_status(task_id):
    """
    获取任务状态
    
    客户端可以定期轮询此接口来获取任务进度
    """
    task = task_service.get_task(task_id)
    
    if not task:
        return api_response(
            success=False,
            error='任务不存在',
            status_code=404
        )
    
    return api_response(
        success=True,
        task=task
    )


@task_bp.route('', methods=['GET'])
@token_required
@handle_exceptions
def get_tasks():
    """
    获取任务列表
    
    支持过滤参数：
    - task_type: 任务类型
    - status: 任务状态
    - limit: 返回数量
    """
    params = get_request_params({
        'task_type': {'type': str, 'required': False},
        'status': {'type': str, 'required': False},
        'limit': {'type': int, 'default': 50}
    })
    
    # 转换状态枚举
    status = None
    if params.get('status'):
        try:
            status = TaskStatus(params['status'])
        except ValueError:
            return api_response(
                success=False,
                error=f"无效的状态值: {params['status']}",
                status_code=400
            )
    
    tasks = task_service.get_all_tasks(
        task_type=params.get('task_type'),
        status=status,
        limit=params['limit']
    )
    
    return api_response(
        success=True,
        tasks=tasks,
        count=len(tasks)
    )


@task_bp.route('/<task_id>/cancel', methods=['POST'])
@token_required
@handle_exceptions
def cancel_task(task_id):
    """取消任务（仅限等待中的任务）"""
    success = task_service.cancel_task(task_id)
    
    if success:
        return api_response(
            success=True,
            message='任务已取消'
        )
    else:
        return api_response(
            success=False,
            error='无法取消任务（任务不存在或已开始执行）',
            status_code=400
        )
