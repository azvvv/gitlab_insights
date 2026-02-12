"""
GitLab 数据同步和查询 API

包含以下功能：
- 数据同步：仓库、组织、分支、权限
- 数据查询：仓库列表、组织列表、分支列表、权限列表
- 分支创建：创建分支（含子模块）
- 分支历史：分支创建历史记录查询
- Tag 创建
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime
from services.gitlab_service import GitlabService
from services.database_service import DatabaseService
from services.gitlab_query_service import GitlabQueryService
from services.task_service import task_service
from dto.tag_create_dto import TagCreateDTO
from middleware.logging_middleware import get_current_user_id
from api.response import api_response, handle_service_result
from api.auth_decorators import token_required, admin_required
from utils.validators import get_request_params
from utils.errorhandler import APIErrorHandler, smart_handle_exceptions, handle_exceptions
from utils.logger import get_logger

logger = get_logger(__name__)

gitlab_bp = Blueprint('gitlab', __name__)
db_service = DatabaseService()
gitlab_query_service = GitlabQueryService()

# ==================== 数据同步 API ====================

@gitlab_bp.route('/sync-repositories', methods=['POST'])
@token_required
@handle_exceptions
def sync_repositories():
    """
    同步 GitLab 仓库数据（异步）
    
    立即返回任务 ID，客户端可通过 /api/tasks/{task_id} 查询进度
    """
    params = get_request_params({
        'async': {'default': 'true'},
        'force': {'default': 'false'}  # 强制执行（忽略防重复检查）
    })
    
    use_async = params['async'].lower() == 'true'
    
    if use_async:
        # 异步执行
        def sync_task():
            gitlab_service = GitlabService()
            return gitlab_service.sync_repositories()
        
        try:
            result = task_service.create_task(
                task_type='sync_repositories',
                func=sync_task,
                allow_duplicate=params['force'].lower() == 'true',
                metadata={
                    'user_id': get_current_user_id() if hasattr(g, 'current_user') else None
                }
            )
            
            return api_response(
                success=True,
                message=result['message'],
                task_id=result['task_id'],
                is_new_task=result['is_new'],
                status_url=f"/api/tasks/{result['task_id']}",
                status_code=202  # 202 Accepted
            )
            
        except ValueError as e:
            # 时间窗口限制
            return api_response(
                success=False,
                error=str(e),
                status_code=429  # Too Many Requests
            )
    else:
        # 同步执行（保持向后兼容）
        gitlab_service = GitlabService()
        result = gitlab_service.sync_repositories()
        result_dict = handle_service_result(result)
        
        status_code = 200 if result_dict.get('success', True) else 500
        return jsonify(result_dict), status_code


@gitlab_bp.route('/sync-groups', methods=['POST'])
@token_required
@handle_exceptions
def sync_groups():
    """同步 GitLab 组织和用户数据（异步）"""
    params = get_request_params({
        'async': {'default': 'true'},
        'force': {'default': 'false'}
    })
    
    use_async = params['async'].lower() == 'true'
    
    if use_async:
        def sync_task():
            gitlab_service = GitlabService()
            return gitlab_service.sync_groups()
        
        try:
            result = task_service.create_task(
                task_type='sync_groups',
                func=sync_task,
                allow_duplicate=params['force'].lower() == 'true',
                metadata={
                    'user_id': get_current_user_id() if hasattr(g, 'current_user') else None
                }
            )
            
            return api_response(
                success=True,
                message=result['message'],
                task_id=result['task_id'],
                is_new_task=result['is_new'],
                status_url=f"/api/tasks/{result['task_id']}",
                status_code=202
            )
            
        except ValueError as e:
            return api_response(
                success=False,
                error=str(e),
                status_code=429
            )
    else:
        gitlab_service = GitlabService()
        result = gitlab_service.sync_groups()
        result_dict = handle_service_result(result)
        
        status_code = 200 if result_dict.get('success', True) else 500
        return jsonify(result_dict), status_code


@gitlab_bp.route('/sync-branches', methods=['POST'])
@token_required
@handle_exceptions
def sync_branches():
    """同步 GitLab 仓库分支数据（异步）"""
    params = get_request_params({
        'repository_id': {'type': int, 'required': False},
        'async': {'default': 'true'},
        'force': {'default': 'false'}
    })
    
    use_async = params['async'].lower() == 'true'
    
    if use_async:
        def sync_task():
            gitlab_service = GitlabService()
            return gitlab_service.sync_repository_branches(params['repository_id'])
        
        try:
            # 包含 repository_id 的任务类型以支持更精细的控制
            task_type = f"sync_branches_{params['repository_id']}" if params['repository_id'] else 'sync_branches'
            
            result = task_service.create_task(
                task_type=task_type,
                func=sync_task,
                allow_duplicate=params['force'].lower() == 'true',
                metadata={
                    'user_id': get_current_user_id() if hasattr(g, 'current_user') else None,
                    'repository_id': params['repository_id']
                }
            )
            
            return api_response(
                success=True,
                message=result['message'],
                task_id=result['task_id'],
                is_new_task=result['is_new'],
                status_url=f"/api/tasks/{result['task_id']}",
                status_code=202
            )
            
        except ValueError as e:
            return api_response(
                success=False,
                error=str(e),
                status_code=429
            )
    else:
        gitlab_service = GitlabService()
        result = gitlab_service.sync_repository_branches(params['repository_id'])
        result_dict = handle_service_result(result)
        
        status_code = 200 if result_dict.get('success', True) else 500
        return jsonify(result_dict), status_code


@gitlab_bp.route('/sync-permissions', methods=['POST'])
@token_required
@handle_exceptions
def sync_permissions():
    """同步 GitLab 仓库权限数据（异步）"""
    params = get_request_params({
        'repository_id': {'type': int, 'required': False},
        'async': {'default': 'true'},
        'force': {'default': 'false'}
    })
    
    use_async = params['async'].lower() == 'true'
    
    if use_async:
        def sync_task():
            gitlab_service = GitlabService()
            return gitlab_service.sync_repository_permissions(params['repository_id'])
        
        try:
            task_type = f"sync_permissions_{params['repository_id']}" if params['repository_id'] else 'sync_permissions'
            
            result = task_service.create_task(
                task_type=task_type,
                func=sync_task,
                allow_duplicate=params['force'].lower() == 'true',
                metadata={
                    'user_id': get_current_user_id() if hasattr(g, 'current_user') else None,
                    'repository_id': params['repository_id']
                }
            )
            
            return api_response(
                success=True,
                message=result['message'],
                task_id=result['task_id'],
                is_new_task=result['is_new'],
                status_url=f"/api/tasks/{result['task_id']}",
                status_code=202
            )
            
        except ValueError as e:
            return api_response(
                success=False,
                error=str(e),
                status_code=429
            )
    else:
        gitlab_service = GitlabService()
        result = gitlab_service.sync_repository_permissions(params['repository_id'])
        result_dict = handle_service_result(result)
        
        status_code = 200 if result_dict.get('success', True) else 500
        return jsonify(result_dict), status_code


@gitlab_bp.route('/sync-all', methods=['POST'])
@token_required
@handle_exceptions
def sync_all():
    """同步所有 GitLab 数据（异步）"""
    params = get_request_params({
        'async': {'default': 'true'},
        'force': {'default': 'false'}
    })
    
    use_async = params['async'].lower() == 'true'
    
    if use_async:
        def sync_task():
            gitlab_service = GitlabService()
            return gitlab_service.sync_all()
        
        try:
            result = task_service.create_task(
                task_type='sync_all',
                func=sync_task,
                allow_duplicate=params['force'].lower() == 'true',
                metadata={
                    'user_id': get_current_user_id() if hasattr(g, 'current_user') else None
                }
            )
            
            return api_response(
                success=True,
                message=result['message'],
                task_id=result['task_id'],
                is_new_task=result['is_new'],
                status_url=f"/api/tasks/{result['task_id']}",
                status_code=202
            )
            
        except ValueError as e:
            return api_response(
                success=False,
                error=str(e),
                status_code=429
            )
    else:
        gitlab_service = GitlabService()
        result = gitlab_service.sync_all()
        result_dict = handle_service_result(result)
        
        status_code = 200 if result_dict.get('success', True) else 500
        return jsonify(result_dict), status_code


# ==================== 数据查询 API ====================

@gitlab_bp.route('/repositories', methods=['GET'])
@handle_exceptions
def get_repositories():
    """获取仓库列表"""
    params = get_request_params({
        'page': {'type': int, 'default': 1},
        'page_size': {'type': int, 'default': 20},
        'search': {'type': str, 'default': None},
        'all': {'type': str, 'default': 'false'}  # 新增：是否返回所有数据
    })
    
    # 调用 service 层
    result = gitlab_query_service.get_repositories(
        page=params['page'],
        page_size=params['page_size'],
        search=params['search'],
        all_records=params['all'].lower() == 'true'
    )
    
    if result.success:
        return api_response(
            repositories=result.data,
            total=result.count,
            page=params['page'],
            page_size=params['page_size']
        )
    else:
        return api_response(
            success=False,
            error=result.error,
            status_code=500
        )


@gitlab_bp.route('/groups', methods=['GET'])
@handle_exceptions
def get_groups():
    """获取组织列表"""
    params = get_request_params({
        'page': {'type': int, 'default': 1},
        'page_size': {'type': int, 'default': 20},
        'search': {'type': str, 'default': None},
        'all': {'type': str, 'default': 'false'}  # 新增：是否返回所有数据
    })
    
    # 调用 service 层
    result = gitlab_query_service.get_groups(
        page=params['page'],
        page_size=params['page_size'],
        search=params['search'],
        all_records=params['all'].lower() == 'true'
    )
    
    if result.success:
        return api_response(
            groups=result.data,
            total=result.count,
            page=params['page'],
            page_size=params['page_size']
        )
    else:
        return api_response(
            success=False,
            error=result.error,
            status_code=500
        )


@gitlab_bp.route('/repository/<int:repo_id>/branches', methods=['GET'])
@handle_exceptions
def get_repository_branches(repo_id):
    """获取仓库分支列表"""
    result = gitlab_query_service.get_repository_branches(repo_id)
    
    if result.success:
        return api_response(**result.data)
    else:
        return api_response(
            success=False,
            error=result.error,
            status_code=500
        )


@gitlab_bp.route('/repository/<int:repo_id>/permissions', methods=['GET'])
@handle_exceptions
def get_repository_permissions(repo_id):
    """获取仓库权限列表"""
    result = gitlab_query_service.get_repository_permissions(repo_id)
    
    if result.success:
        return api_response(**result.data)
    else:
        return api_response(
            success=False,
            error=result.error,
            status_code=500
        )


# ==================== Tag 创建 API ====================

@gitlab_bp.route('/create-tag', methods=['POST'])
@smart_handle_exceptions
def create_tag():
    """创建 GitLab Tag"""
    data = request.get_json()
    if not data:
        return APIErrorHandler.create_error_response(
            error_message='请求体不能为空', 
            status_code=400
        )
    
    try:
        tag_dto = TagCreateDTO(**data)
    except Exception as e:
        return APIErrorHandler.create_error_response(
            error_message=f'参数校验失败: {e}', 
            status_code=400
        )
    
    try:
        gitlab_service = GitlabService()
    except Exception as e:
        return APIErrorHandler.create_error_response(error=e)
    
    result = gitlab_service.create_tag_and_record(tag_dto)
    return APIErrorHandler.handle_service_response(result)


@gitlab_bp.route('/branches', methods=['POST'])
@smart_handle_exceptions
def create_branch_with_submodules():
    """创建分支（包括主仓库和子模块）"""
    data = request.get_json()
    if not data:
        return APIErrorHandler.create_error_response(
            error_message='请求体不能为空', 
            status_code=400
        )
    
    # 验证必需参数
    required_fields = ['project_id', 'new_branch_name', 'source_ref']
    for field in required_fields:
        if field not in data or data.get(field) is None:
            return APIErrorHandler.create_error_response(
                error_message=f'缺少必需参数: {field}，当前值: {data.get(field)}', 
                status_code=400
            )
    
    project_id = data.get('project_id')
    new_branch_name = data.get('new_branch_name')
    source_ref = data.get('source_ref')
    group_name = data.get('group_name', '')
    project_name = data.get('project_name', '')
    jira_ticket = data.get('jira_ticket', None)  # 可选参数
    created_by = data.get('created_by', None)  # 可选参数
    
    logger.info(f"创建分支请求: project_id={project_id}, new_branch_name={new_branch_name}, source_ref={source_ref}, jira_ticket={jira_ticket}")
    
    try:
        gitlab_service = GitlabService()
    except Exception as e:
        return APIErrorHandler.create_error_response(error=e)
    
    try:
        result = gitlab_service.create_branch_with_submodules(
            group_name=group_name,
            project_name=project_name,
            project_id=project_id,
            new_branch_name=new_branch_name,
            ref_branch=source_ref,
            jira_ticket=jira_ticket,
            created_by=created_by
        )
        
        # 检查是否有错误
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'message': '分支创建完成',
            'data': result
        })
    except Exception as e:
        return APIErrorHandler.create_error_response(
            error_message=f'创建分支失败: {str(e)}',
            status_code=500
        )


# ==================== 分支创建历史记录 API ====================

@gitlab_bp.route('/branches/history', methods=['GET'])
@token_required
def get_branch_creation_history():
    """获取分支创建历史记录（带分页和过滤）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)
        
        # 获取过滤参数
        project_id = request.args.get('projectId', type=int)
        status = request.args.get('status', type=str)
        search = request.args.get('search', type=str)
        start_date_str = request.args.get('startDate', type=str)
        end_date_str = request.args.get('endDate', type=str)
        
        # 解析日期
        start_date = None
        end_date = None
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # 调用 GitlabQueryService（只读查询）
        result = gitlab_query_service.get_branch_creation_records(
            page=page,
            page_size=page_size,
            status=status,
            project_id=project_id,
            search=search,
            start_date=start_date,
            end_date=end_date
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'records': result['data'],
                    'total': result['total'],
                    'page': page,
                    'pageSize': page_size,
                    'totalPages': (result['total'] + page_size - 1) // page_size
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error')
            }), 500
    
    except Exception as e:
        logger.exception('Failed to get branch creation records')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gitlab_bp.route('/branches/exists', methods=['GET'])
@token_required
def check_branch_exists():
    """检查分支是否已存在
    
    Query Parameters:
        project_id (int): 项目ID
        branch_name (str): 分支名称
    
    Returns:
        {
            'success': True,
            'data': {
                'exists': bool  # 分支是否存在
            }
        }
    """
    try:
        project_id = request.args.get('project_id', type=int)
        branch_name = request.args.get('branch_name', type=str)
        
        if not project_id or not branch_name:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: project_id and branch_name'
            }), 400
        
        # 调用查询服务检查分支是否存在
        exists = gitlab_query_service.check_branch_exists(project_id, branch_name)
        
        return jsonify({
            'success': True,
            'data': {
                'exists': exists
            }
        })
    
    except Exception as e:
        logger.exception('Failed to check branch existence')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gitlab_bp.route('/branches/history/<int:record_id>', methods=['GET'])
@token_required
def get_branch_creation_record_detail(record_id):
    """获取单个分支创建记录详情"""
    try:
        result = gitlab_query_service.get_branch_creation_record_by_id(record_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data']
            })
        else:
            error_msg = result.get('error', '')
            return jsonify({
                'success': False,
                'error': error_msg
            }), 404 if 'not found' in error_msg.lower() else 500
    
    except Exception as e:
        logger.exception(f'Failed to get branch creation record {record_id}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 待办事项 API ====================

@gitlab_bp.route('/todos', methods=['GET'])
@token_required
@admin_required
@handle_exceptions
def get_todos():
    """
    获取待办事项列表（仅管理员）
    
    Query Parameters:
        state: 状态 ('pending', 'done', 或不传表示全部)
        action: 操作类型 ('assigned', 'review_requested', 'mentioned' 等)
        project_id: 项目ID
        type: 目标类型 ('MergeRequest', 'Issue' 等)
        project_name: 项目名称（部分匹配）
        branch: 目标分支（部分匹配，仅对MR有效）
    """
    params = get_request_params({
        'state': {'type': str, 'default': 'pending'},
        'action': {'type': str, 'default': None},
        'project_id': {'type': int, 'default': None},
        'type': {'type': str, 'default': None},
        'project_name': {'type': str, 'default': None},
        'branch': {'type': str, 'default': None}
    })
    
    # 处理 state 参数
    state = params['state']
    if state == 'all':
        state = None
    
    gitlab_service = GitlabService()
    result = gitlab_service.get_todos(
        state=state,
        action=params['action'],
        project_id=params['project_id'],
        target_type=params['type']
    )
    
    # 客户端过滤（项目名称和分支）
    if result['success'] and result['data']:
        filtered_data = result['data']
        
        # 按项目名称过滤
        if params['project_name']:
            project_name_lower = params['project_name'].lower()
            filtered_data = [
                todo for todo in filtered_data
                if project_name_lower in todo['project']['name_with_namespace'].lower()
            ]
        
        # 按分支过滤
        if params['branch']:
            branch_lower = params['branch'].lower()
            filtered_data = [
                todo for todo in filtered_data
                if todo.get('target_branch') and branch_lower in todo['target_branch'].lower()
            ]
        
        result['data'] = filtered_data
        result['total'] = len(filtered_data)
    
    if result['success']:
        return api_response(
            todos=result['data'],
            total=result['total']
        )
    else:
        return api_response(
            success=False,
            error=result.get('error', '获取待办事项失败'),
            status_code=500
        )


@gitlab_bp.route('/todos/<int:todo_id>/mark-done', methods=['POST'])
@token_required
@admin_required
@handle_exceptions
def mark_todo_done(todo_id):
    """
    标记单个待办事项为完成（仅管理员）
    
    Path Parameters:
        todo_id: 待办事项ID
    """
    gitlab_service = GitlabService()
    result = gitlab_service.mark_todo_done(todo_id)
    
    if result['success']:
        return api_response(
            message=result['message']
        )
    else:
        return api_response(
            success=False,
            error=result.get('error', '标记待办事项失败'),
            status_code=500
        )


@gitlab_bp.route('/todos/mark-all-done', methods=['POST'])
@token_required
@admin_required
@handle_exceptions
def mark_all_todos_done():
    """
    标记所有待办事项为完成（仅管理员）
    """
    gitlab_service = GitlabService()
    result = gitlab_service.mark_all_todos_done()
    
    if result['success']:
        return api_response(
            message=result['message']
        )
    else:
        return api_response(
            success=False,
            error=result.get('error', '标记所有待办事项失败'),
            status_code=500
        )


# ==================== 分支汇总统计 API ====================

@gitlab_bp.route('/branches/summary', methods=['GET'])
@handle_exceptions
def get_branch_summaries():
    """
    获取所有仓库的分支汇总统计（用于前端快速展示）
    
    Query参数:
    - repository_name: 仓库名称（模糊匹配）
    - min_total_branches: 最小分支数
    - has_deletable: 是否有可删除分支（true/false）
    """
    try:
        filters = {}
        
        # 解析查询参数
        if request.args.get('repository_name'):
            filters['repository_name'] = request.args.get('repository_name')
        
        if request.args.get('min_total_branches'):
            filters['min_total_branches'] = int(request.args.get('min_total_branches'))
        
        if request.args.get('has_deletable'):
            filters['has_deletable'] = request.args.get('has_deletable').lower() == 'true'
        
        result = gitlab_query_service.get_branch_summaries(filters)
        
        if result['success']:
            return api_response(
                data=result['data'],
                total=result['total']
            )
        else:
            return api_response(
                success=False,
                error=result.get('error', '获取分支汇总失败'),
                status_code=500
            )
    except Exception as e:
        logger.exception('获取分支汇总失败')
        return api_response(
            success=False,
            error=str(e),
            status_code=500
        )


@gitlab_bp.route('/branches/summary/global', methods=['GET'])
@handle_exceptions
def get_global_branch_statistics():
    """获取全局分支统计信息"""
    try:
        result = gitlab_query_service.get_global_branch_statistics()
        
        if result['success']:
            return api_response(data=result['data'])
        else:
            return api_response(
                success=False,
                error=result.get('error', '获取全局统计失败'),
                status_code=500
            )
    except Exception as e:
        logger.exception('获取全局分支统计失败')
        return api_response(
            success=False,
            error=str(e),
            status_code=500
        )


@gitlab_bp.route('/branches/summary/repository/<int:repo_id>', methods=['GET'])
@handle_exceptions
def get_repository_branch_summary(repo_id):
    """获取指定仓库的分支汇总"""
    try:
        result = gitlab_query_service.get_branch_summary_by_repository(repo_id)
        
        if result['success']:
            return api_response(data=result['data'])
        else:
            return api_response(
                success=False,
                error=result.get('error', '获取仓库分支汇总失败'),
                status_code=404 if '不存在' in result.get('error', '') else 500
            )
    except Exception as e:
        logger.exception(f'获取仓库 {repo_id} 的分支汇总失败')
        return api_response(
            success=False,
            error=str(e),
            status_code=500
        )


@gitlab_bp.route('/branches/summary/generate', methods=['POST'])
@token_required
@handle_exceptions
def generate_branch_summaries():
    """
    生成所有仓库的分支汇总统计（异步）
    
    Body参数:
    - force_refresh: 是否强制刷新（删除旧数据重新生成）默认 false
    - async: 是否异步执行，默认 true
    """
    try:
        data = request.get_json() or {}
        force_refresh = data.get('force_refresh', False)
        use_async = data.get('async', True)
        
        if use_async:
            # 异步执行
            def generate_task():
                gitlab_service = GitlabService()
                return gitlab_service.generate_branch_summaries(force_refresh)
            
            result = task_service.create_task(
                task_type='generate_branch_summaries',
                func=generate_task,
                allow_duplicate=False,
                metadata={
                    'user_id': get_current_user_id() if hasattr(g, 'current_user') else None,
                    'force_refresh': force_refresh
                }
            )
            
            return api_response(
                success=True,
                message=result['message'],
                task_id=result['task_id'],
                is_new_task=result['is_new'],
                status_url=f"/api/tasks/{result['task_id']}",
                status_code=202
            )
        else:
            # 同步执行
            gitlab_service = GitlabService()
            result = gitlab_service.generate_branch_summaries(force_refresh)
            
            if result['success']:
                return api_response(
                    message=result['message'],
                    data={
                        'total_repositories': result['total_repositories'],
                        'success_count': result['success_count'],
                        'error_count': result['error_count']
                    }
                )
            else:
                return api_response(
                    success=False,
                    error=result.get('error', '生成分支汇总失败'),
                    status_code=500
                )
    except Exception as e:
        logger.exception('生成分支汇总失败')
        return api_response(
            success=False,
            error=str(e),
            status_code=500
        )


@gitlab_bp.route('/branches/summary/repository/<int:repo_id>/generate', methods=['POST'])
@token_required
@handle_exceptions
def generate_repository_summary(repo_id):
    """生成指定仓库的分支汇总"""
    try:
        gitlab_service = GitlabService()
        result = gitlab_service.generate_repository_summary(repo_id)
        
        if result['success']:
            return api_response(
                message=result['message'],
                data=result.get('data')
            )
        else:
            return api_response(
                success=False,
                error=result.get('error', '生成仓库分支汇总失败'),
                status_code=404 if '不存在' in result.get('error', '') else 500
            )
    except Exception as e:
        logger.exception(f'生成仓库 {repo_id} 的分支汇总失败')
        return api_response(
            success=False,
            error=str(e),
            status_code=500
        )
