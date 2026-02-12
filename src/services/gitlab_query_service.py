"""
GitLab 数据查询服务
处理 GitLab 相关的数据库查询操作（只读操作）

职责：
- 查询仓库、组织、分支、权限等信息
- 提供数据检索和搜索功能
- 不涉及任何写操作和 GitLab API 调用
"""
from typing import Optional, Dict, List, Any
from sqlalchemy import or_
from database.connection import get_db_session
from database.models import (
    GitlabRepository, GitlabGroup, GitlabRepositoryBranch, 
    GitlabRepositoryPermission, GitlabBranchRule
)
from dto.base_dto import BaseResult, CountableResult
from utils.logger import get_logger

logger = get_logger(__name__)


class GitlabQueryService:
    """GitLab 查询服务"""
    
    def __init__(self):
        pass
    
    def get_repositories(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        all_records: bool = False
    ) -> CountableResult:
        """
        获取仓库列表
        
        Args:
            page: 页码
            page_size: 每页数量
            search: 搜索关键词
            all_records: 是否返回所有记录（不分页）
        """
        try:
            with get_db_session() as db:
                # 构建查询
                query = db.query(GitlabRepository)
                
                # 搜索过滤
                if search:
                    search_pattern = f"%{search}%"
                    query = query.filter(
                        (GitlabRepository.name.ilike(search_pattern)) |
                        (GitlabRepository.name_with_namespace.ilike(search_pattern)) |
                        (GitlabRepository.description.ilike(search_pattern))
                    )
                
                # 获取总数
                total = query.count()
                
                # 是否返回所有数据
                if all_records:
                    repos = query.order_by(GitlabRepository.id).all()
                else:
                    # 分页
                    offset = (page - 1) * page_size
                    repos = query.order_by(GitlabRepository.id).offset(offset).limit(page_size).all()
                
                # 格式化数据
                repositories = []
                for repo in repos:
                    # 从 name_with_namespace 提取 namespace
                    namespace_full_path = ''
                    if repo.name_with_namespace:
                        parts = repo.name_with_namespace.rsplit('/', 1)
                        if len(parts) == 2:
                            namespace_full_path = parts[0]
                    
                    repo_dict = {
                        'id': repo.id,
                        'name': repo.name,
                        'name_with_namespace': repo.name_with_namespace,
                        'namespace_full_path': namespace_full_path,
                        'description': repo.description,
                        'web_url': repo.web_url,
                        'default_branch': repo.default_branch,
                        'visibility': repo.visibility,
                        'created_at': repo.created_at.isoformat() if repo.created_at else None,
                        'last_activity_at': repo.last_activity_at.isoformat() if repo.last_activity_at else None,
                        'sync_time': repo.sync_time.isoformat()
                    }
                    repositories.append(repo_dict)
                
                return CountableResult.create_success(
                    data=repositories,
                    count=total,
                    message=f"Found {total} repositories"
                )
                
        except Exception as e:
            logger.exception('Failed to get repositories')
            return CountableResult.create_failure(str(e))
    
    def get_groups(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        all_records: bool = False
    ) -> CountableResult:
        """
        获取组织列表
        
        Args:
            page: 页码
            page_size: 每页数量
            search: 搜索关键词
            all_records: 是否返回所有记录（不分页）
        """
        try:
            with get_db_session() as db:
                # 构建查询
                query = db.query(GitlabGroup)
                
                # 搜索过滤
                if search:
                    search_pattern = f"%{search}%"
                    query = query.filter(
                        (GitlabGroup.name.ilike(search_pattern)) |
                        (GitlabGroup.path.ilike(search_pattern)) |
                        (GitlabGroup.description.ilike(search_pattern))
                    )
                
                # 获取总数
                total = query.count()
                
                # 是否返回所有数据
                if all_records:
                    groups = query.order_by(GitlabGroup.id).all()
                else:
                    # 分页
                    offset = (page - 1) * page_size
                    groups = query.order_by(GitlabGroup.id).offset(offset).limit(page_size).all()
                
                # 格式化数据
                groups_list = []
                for group in groups:
                    group_dict = {
                        'id': group.id,
                        'name': group.name,
                        'path': group.path,
                        'full_path': group.path,  # 添加 full_path 字段
                        'description': group.description,
                        'web_url': group.web_url,
                        'visibility': group.visibility,
                        'created_at': group.created_at.isoformat() if group.created_at else None,
                        'sync_time': group.sync_time.isoformat(),
                        'member_count': len(group.members) if hasattr(group, 'members') else 0
                    }
                    groups_list.append(group_dict)
                
                return CountableResult.create_success(
                    data=groups_list,
                    count=total,
                    message=f"Found {total} groups"
                )
                
        except Exception as e:
            logger.exception('Failed to get groups')
            return CountableResult.create_failure(str(e))
    
    def get_repository_branches(self, repo_id: int) -> BaseResult:
        """
        获取仓库分支列表
        
        Args:
            repo_id: 仓库ID
        """
        try:
            with get_db_session() as db:
                branches = db.query(GitlabRepositoryBranch).filter(
                    GitlabRepositoryBranch.repository_id == repo_id
                ).all()
                
                branches_list = []
                for branch in branches:
                    branch_dict = {
                        'branch_name': branch.branch_name,
                        'commit_id': branch.commit_id,
                        'commit_message': branch.commit_message,
                        'commit_author_name': branch.commit_author_name,
                        'commit_author_email': branch.commit_author_email,
                        'last_commit_date': branch.last_commit_date.isoformat() if branch.last_commit_date else None,
                        'protected': branch.protected,
                        'sync_time': branch.sync_time.isoformat()
                    }
                    branches_list.append(branch_dict)
                
                return BaseResult.create_success(
                    data={
                        'repository_id': repo_id,
                        'branches': branches_list,
                        'count': len(branches_list)
                    },
                    message=f"Found {len(branches_list)} branches for repository {repo_id}"
                )
                
        except Exception as e:
            logger.exception(f'Failed to get branches for repository {repo_id}')
            return BaseResult.create_failure(str(e))
    
    def get_repository_permissions(self, repo_id: int) -> BaseResult:
        """
        获取仓库权限列表
        
        Args:
            repo_id: 仓库ID
        """
        try:
            with get_db_session() as db:
                permissions = db.query(GitlabRepositoryPermission).filter(
                    GitlabRepositoryPermission.repository_id == repo_id
                ).all()
                
                permissions_list = []
                for perm in permissions:
                    perm_dict = {
                        'member_type': perm.member_type,
                        'member_id': perm.member_id,
                        'member_name': perm.member_name,
                        'access_level': perm.access_level,
                        'access_level_name': perm.access_level_name,
                        'sync_time': perm.sync_time.isoformat()
                    }
                    permissions_list.append(perm_dict)
                
                return BaseResult.create_success(
                    data={
                        'repository_id': repo_id,
                        'permissions': permissions_list,
                        'count': len(permissions_list)
                    },
                    message=f"Found {len(permissions_list)} permissions for repository {repo_id}"
                )
                
        except Exception as e:
            logger.exception(f'Failed to get permissions for repository {repo_id}')
            return BaseResult.create_failure(str(e))
    
    def get_repository_by_id(self, repo_id: int) -> Optional[GitlabRepository]:
        """
        根据 ID 查询单个仓库
        
        Args:
            repo_id: 仓库ID
            
        Returns:
            仓库对象或 None
        """
        try:
            with get_db_session() as db:
                return db.query(GitlabRepository).filter(
                    GitlabRepository.id == repo_id
                ).first()
        except Exception as e:
            logger.exception(f'Failed to get repository by id {repo_id}')
            return None
    
    def find_repository_by_name(self, name: str, use_fuzzy: bool = True) -> Optional[GitlabRepository]:
        """
        根据名称查找仓库（支持多种匹配方式）
        
        Args:
            name: 仓库名称或路径
            use_fuzzy: 是否使用模糊匹配
            
        Returns:
            仓库对象或 None
        """
        try:
            with get_db_session() as db:
                # 规范化名称
                normalized = name.strip().strip('/')
                
                # 1. 精确匹配 name_with_namespace
                repo_obj = db.query(GitlabRepository).filter(
                    GitlabRepository.name_with_namespace == normalized
                ).first()
                
                if repo_obj:
                    return repo_obj
                
                # 2. 如果开启模糊匹配
                if use_fuzzy:
                    simple_name = normalized.split('/')[-1]
                    
                    # 尝试通过 http_url_to_repo 匹配
                    repo_obj = db.query(GitlabRepository).filter(
                        GitlabRepository.http_url_to_repo.like(f"%{simple_name}%")
                    ).first()
                    
                    if repo_obj:
                        return repo_obj
                    
                    # 尝试通过 web_url 匹配
                    repo_obj = db.query(GitlabRepository).filter(
                        GitlabRepository.web_url.like(f"%{simple_name}%")
                    ).first()
                    
                    if repo_obj:
                        return repo_obj
                    
                    # 尝试通过 name 匹配
                    repo_obj = db.query(GitlabRepository).filter(
                        GitlabRepository.name == simple_name
                    ).first()
                    
                    return repo_obj
                
                return None
                
        except Exception as e:
            logger.exception(f'Failed to find repository by name {name}')
            return None
    
    def get_repository_branches_and_rules(self, repository_id: int) -> Dict[str, Any]:
        """
        获取仓库的分支和规则（用于分支分析）
        
        Args:
            repository_id: 仓库ID
            
        Returns:
            包含分支和规则的字典
        """
        try:
            with get_db_session() as db:
                # 获取该仓库的所有分支
                branches = db.query(GitlabRepositoryBranch).filter(
                    GitlabRepositoryBranch.repository_id == repository_id
                ).all()
                
                # 获取所有启用的规则
                rules = db.query(GitlabBranchRule).filter(
                    GitlabBranchRule.is_active == True
                ).order_by(GitlabBranchRule.priority.desc()).all()
                
                return {
                    'branches': branches,
                    'rules': rules
                }
                
        except Exception as e:
            logger.exception(f'Failed to get branches and rules for repository {repository_id}')
            return {
                'branches': [],
                'rules': []
            }
    
    def check_branch_exists(self, project_id: int, branch_name: str) -> bool:
        """
        检查指定仓库中分支是否存在
        
        Args:
            project_id: 仓库ID
            branch_name: 分支名称
            
        Returns:
            True 如果分支存在，False 否则
        """
        try:
            with get_db_session() as db:
                branch = db.query(GitlabRepositoryBranch).filter(
                    GitlabRepositoryBranch.repository_id == project_id,
                    GitlabRepositoryBranch.branch_name == branch_name
                ).first()
                
                return branch is not None
                
        except Exception as e:
            logger.exception(f'Failed to check branch existence: {project_id}/{branch_name}')
            # 出错时返回 False，让后端再次检查
            return False
    
    def get_branch_creation_records(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        project_id: Optional[int] = None,
        search: Optional[str] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        获取分支创建记录（带分页和过滤）
        
        Args:
            page: 页码
            page_size: 每页大小
            status: 状态过滤
            project_id: 项目ID过滤
            search: 搜索关键词
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            {
                'success': bool,
                'data': [...],
                'total': int,
                'error': str
            }
        """
        from database.models import GitlabBranchCreateRecord
        from sqlalchemy import desc, or_
        
        try:
            with get_db_session() as db:
                # 基础查询
                query = db.query(GitlabBranchCreateRecord).join(
                    GitlabRepository,
                    GitlabBranchCreateRecord.project_id == GitlabRepository.id
                )
                
                # 应用过滤条件
                if status:
                    query = query.filter(GitlabBranchCreateRecord.status == status)
                
                if project_id:
                    query = query.filter(GitlabBranchCreateRecord.project_id == project_id)
                
                if search:
                    query = query.filter(
                        or_(
                            GitlabBranchCreateRecord.branch_name.ilike(f'%{search}%'),
                            GitlabRepository.name.ilike(f'%{search}%'),
                            GitlabBranchCreateRecord.jira_ticket.ilike(f'%{search}%')
                        )
                    )
                
                if start_date:
                    query = query.filter(GitlabBranchCreateRecord.created_at >= start_date)
                
                if end_date:
                    query = query.filter(GitlabBranchCreateRecord.created_at <= end_date)
                
                # 获取总数
                total = query.count()
                
                # 分页
                records = query.order_by(
                    desc(GitlabBranchCreateRecord.created_at)
                ).offset((page - 1) * page_size).limit(page_size).all()
                
                # 构建返回数据
                records_data = []
                for record in records:
                    repo = db.query(GitlabRepository).filter(
                        GitlabRepository.id == record.project_id
                    ).first()
                    
                    records_data.append({
                        'id': record.id,
                        'project_id': record.project_id,
                        'project_name': repo.name if repo else 'Unknown',
                        'project_path': repo.name_with_namespace if repo else 'Unknown',
                        'branch_name': record.branch_name,
                        'source_ref': record.source_ref,
                        'source_commit': record.source_commit,
                        'status': record.status,
                        'message': record.message,
                        'jira_ticket': record.jira_ticket,
                        'created_by': record.created_by,
                        'created_at': record.created_at.isoformat() if record.created_at else None
                    })
                
                return {
                    'success': True,
                    'data': records_data,
                    'total': total
                }
                
        except Exception as e:
            logger.exception('Failed to get branch creation records')
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_branch_creation_record_by_id(self, record_id: int) -> Dict[str, Any]:
        """
        获取单个分支创建记录详情
        
        Args:
            record_id: 记录ID
            
        Returns:
            {
                'success': bool,
                'data': {...},
                'error': str
            }
        """
        from database.models import GitlabBranchCreateRecord
        
        try:
            with get_db_session() as db:
                record = db.query(GitlabBranchCreateRecord).filter(
                    GitlabBranchCreateRecord.id == record_id
                ).first()
                
                if not record:
                    return {
                        'success': False,
                        'error': f"Record with ID {record_id} not found"
                    }
                
                repo = db.query(GitlabRepository).filter(
                    GitlabRepository.id == record.project_id
                ).first()
                
                record_data = {
                    'id': record.id,
                    'project_id': record.project_id,
                    'project_name': repo.name if repo else 'Unknown',
                    'project_path': repo.name_with_namespace if repo else 'Unknown',
                    'branch_name': record.branch_name,
                    'source_ref': record.source_ref,
                    'source_commit': record.source_commit,
                    'status': record.status,
                    'message': record.message,
                    'created_at': record.created_at.isoformat() if record.created_at else None,
                    'created_by': record.created_by,
                    'jira_ticket': record.jira_ticket
                }
                
                return {
                    'success': True,
                    'data': record_data
                }
                
        except Exception as e:
            logger.exception(f'Failed to get record {record_id}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_branch_summaries(self, filters: dict = None) -> dict:
        """获取所有仓库的分支汇总（支持筛选）"""
        from database.models import GitlabBranchSummary
        
        try:
            with get_db_session() as db:
                query = db.query(GitlabBranchSummary)
                
                # 应用筛选条件
                if filters:
                    if 'min_total_branches' in filters:
                        query = query.filter(
                            GitlabBranchSummary.total_branches >= filters['min_total_branches']
                        )
                    
                    if 'repository_name' in filters and filters['repository_name']:
                        query = query.filter(
                            GitlabBranchSummary.repository_name.like(f"%{filters['repository_name']}%")
                        )
                    
                    if 'has_deletable' in filters and filters['has_deletable']:
                        query = query.filter(GitlabBranchSummary.deletable_branches > 0)
                
                # 按总分支数降序排列
                summaries = query.order_by(GitlabBranchSummary.total_branches.desc()).all()
                
                return {
                    'success': True,
                    'total': len(summaries),
                    'data': [s.to_dict() for s in summaries]
                }
                
        except Exception as e:
            logger.exception('Failed to get branch summaries')
            return {
                'success': False,
                'error': str(e),
                'data': []
            }
    
    def get_branch_summary_by_repository(self, repository_id: int) -> dict:
        """获取指定仓库的分支汇总"""
        from database.models import GitlabBranchSummary
        
        try:
            with get_db_session() as db:
                summary = db.query(GitlabBranchSummary).filter_by(
                    repository_id=repository_id
                ).first()
                
                if not summary:
                    return {
                        'success': False,
                        'error': f'仓库 {repository_id} 的分支汇总不存在，请先生成'
                    }
                
                return {
                    'success': True,
                    'data': summary.to_dict()
                }
                
        except Exception as e:
            logger.exception(f'Failed to get branch summary for repository {repository_id}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_global_branch_statistics(self) -> dict:
        """获取全局分支统计信息"""
        from database.models import GitlabBranchSummary
        from sqlalchemy import func
        
        try:
            with get_db_session() as db:
                # 聚合统计
                stats = db.query(
                    func.count(GitlabBranchSummary.id).label('total_repositories'),
                    func.sum(GitlabBranchSummary.total_branches).label('total_branches'),
                    func.sum(GitlabBranchSummary.protected_branches).label('total_protected'),
                    func.sum(GitlabBranchSummary.deletable_branches).label('total_deletable'),
                    func.sum(GitlabBranchSummary.feature_branches).label('total_feature'),
                    func.sum(GitlabBranchSummary.release_branches).label('total_release'),
                    func.sum(GitlabBranchSummary.hotfix_branches).label('total_hotfix'),
                    func.sum(GitlabBranchSummary.active_30days).label('total_active_30days'),
                    func.sum(GitlabBranchSummary.active_90days).label('total_active_90days'),
                    func.sum(GitlabBranchSummary.inactive_180days).label('total_inactive_180days'),
                    func.sum(GitlabBranchSummary.inactive_365days).label('total_inactive_365days'),
                ).first()
                
                return {
                    'success': True,
                    'data': {
                        'total_repositories': stats.total_repositories or 0,
                        'total_branches': stats.total_branches or 0,
                        'total_protected': stats.total_protected or 0,
                        'total_deletable': stats.total_deletable or 0,
                        'total_feature': stats.total_feature or 0,
                        'total_release': stats.total_release or 0,
                        'total_hotfix': stats.total_hotfix or 0,
                        'total_active_30days': stats.total_active_30days or 0,
                        'total_active_90days': stats.total_active_90days or 0,
                        'total_inactive_180days': stats.total_inactive_180days or 0,
                        'total_inactive_365days': stats.total_inactive_365days or 0,
                    }
                }
                
        except Exception as e:
            logger.exception('Failed to get global branch statistics')
            return {
                'success': False,
                'error': str(e)
            }
