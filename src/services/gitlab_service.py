import os
import re
import shutil
import subprocess
import tempfile
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional

import gitlab

from config.settings import settings
from database.connection import get_db_session
from database.models import (
    GitlabBranchRule,
    GitlabRepository,
    GitlabRepositoryBranch,
    GitlabSubmoduleUpdateRecord,
    GitlabTagRelation,
)
from dto.gitlab_data_dto import (
    GitlabBranchData,
    GitlabGroupData,
    GitlabMemberData,
    GitlabPermissionData,
    GitlabRepositoryData,
)
from dto.sync_dto import AllSyncResult, BranchSyncResult, GroupSyncResult, SyncResult
from dto.tag_create_dto import TagCreateDTO
from services.database_service import DatabaseService
from utils.logger import get_logger

logger = get_logger(__name__, 'gitlab')

class GitlabService:
    def get_todos(self, state: str = 'pending', action: str = None, 
                  project_id: int = None, target_type: str = None) -> Dict[str, Any]:
        """
        获取当前用户的待办事项列表
        
        Args:
            state: 状态 ('pending', 'done', 或 None 表示全部)
            action: 操作类型过滤
            project_id: 项目ID过滤
            target_type: 目标类型过滤 ('MergeRequest', 'Issue' 等)
        
        Returns:
            {
                'success': bool,
                'data': [...],
                'total': int
            }
        """
        try:
            # 构建查询参数
            params = {}
            if state:
                params['state'] = state
            if action:
                params['action'] = action
            if project_id:
                params['project_id'] = project_id
            if target_type:
                params['type'] = target_type
            
            # 获取所有待办事项
            todos = self.gl.todos.list(**params, get_all=True)
            
            # 格式化数据
            formatted_todos = []
            for todo in todos:
                todo_dict = {
                    'id': todo.id,
                    'state': todo.state,
                    'action': todo.action_name,
                    'action_name': self._get_action_display_name(todo.action_name),
                    'target_type': todo.target_type,
                    'title': todo.body if hasattr(todo, 'body') else 'N/A',
                    'body': todo.body if hasattr(todo, 'body') else '',
                    'author': {
                        'id': todo.author.get('id') if hasattr(todo, 'author') and isinstance(todo.author, dict) else None,
                        'name': todo.author.get('name') if hasattr(todo, 'author') and isinstance(todo.author, dict) else 'Unknown',
                        'username': todo.author.get('username') if hasattr(todo, 'author') and isinstance(todo.author, dict) else 'unknown'
                    },
                    'project': {
                        'id': todo.project.get('id') if hasattr(todo, 'project') and isinstance(todo.project, dict) else None,
                        'name': todo.project.get('name') if hasattr(todo, 'project') and isinstance(todo.project, dict) else 'Unknown',
                        'name_with_namespace': todo.project.get('name_with_namespace') if hasattr(todo, 'project') and isinstance(todo.project, dict) else 'Unknown'
                    },
                    'target': todo.target if hasattr(todo, 'target') and isinstance(todo.target, dict) else {},
                    'target_url': todo.target_url if hasattr(todo, 'target_url') else '',
                    'created_at': todo.created_at if hasattr(todo, 'created_at') else None
                }
                
                # 如果是MR，获取分支信息
                if todo.target_type == 'MergeRequest':
                    try:
                        mr_iid = todo.target.get('iid') if isinstance(todo.target, dict) else None
                        project_id = todo.project.get('id') if isinstance(todo.project, dict) else None
                        
                        if mr_iid and project_id:
                            project = self.gl.projects.get(project_id)
                            mr = project.mergerequests.get(mr_iid)
                            todo_dict['source_branch'] = mr.source_branch
                            todo_dict['target_branch'] = mr.target_branch
                        else:
                            todo_dict['source_branch'] = None
                            todo_dict['target_branch'] = None
                    except Exception as e:
                        logger.warning(f"获取MR分支信息失败: {str(e)}")
                        todo_dict['source_branch'] = None
                        todo_dict['target_branch'] = None
                else:
                    todo_dict['source_branch'] = None
                    todo_dict['target_branch'] = None
                
                formatted_todos.append(todo_dict)
            
            return {
                'success': True,
                'data': formatted_todos,
                'total': len(formatted_todos)
            }
            
        except Exception as e:
            logger.error(f"获取待办事项失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'total': 0
            }
    
    def mark_todo_done(self, todo_id: int) -> Dict[str, Any]:
        """
        标记单个待办事项为完成
        
        Args:
            todo_id: 待办事项ID
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # 先获取所有待办事项，找到对应的 todo 对象
            # python-gitlab 的 TodoManager 不支持 get() 方法，需要通过 list 查找
            todos = self.gl.todos.list(state='pending', get_all=True)
            
            todo_found = None
            for todo in todos:
                if todo.id == todo_id:
                    todo_found = todo
                    break
            
            if not todo_found:
                # 如果在 pending 中没找到，可能已经完成或不存在
                return {
                    'success': False,
                    'error': f'待办事项 #{todo_id} 不存在或已完成'
                }
            
            # 使用 Todo 对象的 mark_as_done 方法
            todo_found.mark_as_done()
            
            return {
                'success': True,
                'message': f'待办事项 #{todo_id} 已标记为完成'
            }
                
        except Exception as e:
            logger.error(f"标记待办事项失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def mark_all_todos_done(self) -> Dict[str, Any]:
        """
        标记所有待办事项为完成
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # 获取所有待处理的待办事项
            todos = self.gl.todos.list(state='pending', get_all=True)
            
            if not todos:
                return {
                    'success': True,
                    'message': '没有待处理的待办事项'
                }
            
            # 逐个标记为完成
            marked_count = 0
            failed_count = 0
            
            for todo in todos:
                try:
                    todo.mark_as_done()
                    marked_count += 1
                except Exception as e:
                    logger.warning(f"标记待办事项 #{todo.id} 失败: {str(e)}")
                    failed_count += 1
            
            if failed_count == 0:
                return {
                    'success': True,
                    'message': f'成功标记 {marked_count} 个待办事项为完成'
                }
            else:
                return {
                    'success': True,
                    'message': f'标记完成 {marked_count} 个，失败 {failed_count} 个'
                }
                
        except Exception as e:
            logger.error(f"标记所有待办事项失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_action_display_name(self, action: str) -> str:
        """将操作类型转换为显示名称"""
        action_map = {
            'assigned': '分配给你',
            'mentioned': '提到了你',
            'build_failed': '构建失败',
            'marked': '标记',
            'approval_required': '需要审批',
            'unmergeable': '无法合并',
            'directly_addressed': '直接提到',
            'merge_train_removed': '合并列车移除',
            'review_requested': '请求审查'
        }
        return action_map.get(action, action)

    def __init__(self, gitlab_url=None, gitlab_token=None):
        # 优先使用传入参数，否则使用统一配置
        self.gitlab_url = gitlab_url or settings.gitlab.url
        self.gitlab_token = gitlab_token or settings.gitlab.token
        self.db_service = DatabaseService()
        
        # 延迟导入以避免循环依赖
        from services.gitlab_query_service import GitlabQueryService
        self.query_service = GitlabQueryService()
        
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''
        
        # 配置已在 settings 中验证，初始化 GitLab 客户端
        try:
            logger.info(f"正在连接 GitLab: {self.gitlab_url}")
            self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.gitlab_token)
            self.gl.auth()  # 验证连接
            logger.info("GitLab 连接成功")
        except gitlab.exceptions.GitlabAuthenticationError as e:
            # 401 认证错误 - Token 无效或过期
            error_msg = "GitLab 认证失败 (401 Unauthorized)"
            logger.error(f"{error_msg}. 请检查 GITLAB_TOKEN 配置: Token 是否过期、权限是否足够、URL 是否正确: {self.gitlab_url}")
            raise ValueError(error_msg) from e
        except gitlab.exceptions.GitlabHttpError as e:
            # 其他 HTTP 错误（403, 404, 500 等）
            error_msg = f"GitLab HTTP 错误 ({e.response_code}): {e.error_message}"
            logger.error(f"{error_msg}. GitLab URL: {self.gitlab_url}")
            raise ValueError(error_msg) from e
        except Exception as e:
            # 其他未知错误
            error_msg = f"GitLab 连接失败: {type(e).__name__}: {str(e)}"
            logger.error(f"{error_msg}. GitLab URL: {self.gitlab_url}. 请检查配置和网络连接", exc_info=True)
            raise ValueError(error_msg) from e
    
    def sync_repositories(self) -> SyncResult:
        """同步所有仓库信息"""
        logger.info("开始同步仓库信息...")
        
        try:
            print("Starting repository sync...")
            
            # 获取所有项目
            projects = self.gl.projects.list(
                statistics=True,
                all=True
            )
            
            logger.info(f"从 GitLab 获取到 {len(projects)} 个项目")
            print(f"Found {len(projects)} projects from GitLab")
            
            # 转换为 DTO 格式
            repositories = []
            for project in projects:
                try:
                    repo_dto = GitlabRepositoryData.from_model(project)  # 修正：使用 from_model
                    repositories.append(repo_dto.to_dict())
                except Exception as e:
                    print(f"Error processing project {project.id}: {e}")
                    continue
            
            print(f"Prepared {len(repositories)} repositories for sync")
            
            # 同步到数据库
            sync_result = self.db_service.sync_repositories(repositories)
            
            if sync_result.success:
                print(f"Successfully synced {sync_result.count} repositories")  # 修正：使用 count 属性
                return SyncResult.create_success(
                    sync_result.count,  # 修正：使用 count 属性
                    len(repositories)
                )
            else:
                return SyncResult.create_failure(sync_result.error)  # 修正：使用 error 属性
            
        except Exception as e:
            print(f"Error syncing repositories: {e}")
            traceback.print_exc()
            return SyncResult.create_failure(str(e))
    
    def sync_groups(self) -> GroupSyncResult:
        """同步所有组织及其用户信息"""
        try:
            print("Starting groups sync...")
            
            # 获取所有组织
            groups = self.gl.groups.list(all=True, statistics=True)
            
            synced_groups = 0
            synced_members = 0
            
            for group in groups:
                try:
                    # 转换组织数据为 DTO
                    group_dto = GitlabGroupData.from_model(group)  # 修正：使用 from_model
                    
                    # 同步组织信息
                    group_result = self.db_service.sync_group(group_dto.to_dict())
                    if group_result.success:
                        synced_groups += 1
                    
                    # 同步组织成员
                    try:
                        members = group.members.list(all=True)
                        members_data = []
                        for member in members:
                            member_dto = GitlabMemberData.from_model(member)  # 修正：使用 from_model
                            members_data.append(member_dto.to_dict())
                        
                        member_sync_result = self.db_service.sync_group_members(group.id, members_data)
                        if member_sync_result.success:
                            synced_members += member_sync_result.count  # 修正：使用 count 属性
                            print(f"Synced {member_sync_result.count} members for group {group.name}")
                        
                    except Exception as e:
                        print(f"Error syncing members for group {group.name}: {e}")
                
                except Exception as e:
                    print(f"Error processing group {group.id}: {e}")
                    continue
            
            print(f"Successfully synced {synced_groups} groups and {synced_members} members")
            return GroupSyncResult.create_success(
                synced_groups, 
                synced_members, 
                len(groups)
            )
            
        except Exception as e:
            print(f"Error syncing groups: {e}")
            return GroupSyncResult.create_failure(str(e))
    
    def sync_repository_branches(self, repository_id: int = None) -> BranchSyncResult:
        """同步仓库分支信息"""
        try:
            if repository_id:
                try:
                    project = self.gl.projects.get(repository_id)
                    repositories = [project]
                except gitlab.exceptions.GitlabGetError:
                    return BranchSyncResult.create_failure(
                        f'Repository {repository_id} not found'
                    )
            else:
                # 从数据库获取已同步的仓库
                repo_ids = self.db_service.get_all_repository_ids()
                if not repo_ids:
                    return BranchSyncResult.create_failure(
                        'No repositories found in database. Please sync repositories first.'
                    )
                
                repositories = []
                for repo_id_obj in repo_ids:
                    try:
                        project = self.gl.projects.get(repo_id_obj.id)
                        repositories.append(project)
                    except Exception as e:
                        print(f"Error getting project {repo_id_obj.id}: {e}")
                        continue
            
            print(f"Starting branches sync for {len(repositories)} repositories...")
            
            total_synced = 0
            processed_repos = 0
            
            for project in repositories:
                try:
                    print(f"Processing branches for repository {project.id} ({project.name})")
                    
                    # 获取分支列表
                    branches = project.branches.list(all=True)
                    print(f"Found {len(branches)} branches for repository {project.id}")
                    
                    branch_data = []
                    for branch in branches:
                        try:
                            # 获取提交详情
                            commit = project.commits.get(branch.commit['id'])
                            branch_dto = GitlabBranchData.from_model(branch, commit)  # 修正：使用 from_model
                        except Exception as e:
                            print(f"Error getting commit info for branch {branch.name}: {e}")
                            # 使用基本信息
                            branch_dto = GitlabBranchData.from_model(branch)  # 修正：使用 from_model
                        
                        branch_data.append(branch_dto.to_dict())
                    
                    sync_result = self.db_service.sync_repository_branches(project.id, branch_data)
                    if sync_result.success:
                        # 同步完成后立即分析分支规则
                        self._analyze_repository_branches(project.id)
                        
                        total_synced += sync_result.count
                        processed_repos += 1
                        print(f"Synced and analyzed {sync_result.count} branches for repository {project.id}")
                    
                except Exception as e:
                    print(f"Error syncing branches for repository {project.id}: {e}")
                    continue
            
            print(f"Successfully synced {total_synced} branches for {processed_repos} repositories")
            return BranchSyncResult.create_success(
                total_synced, 
                processed_repos, 
                len(repositories)
            )
            
        except Exception as e:
            print(f"Error syncing repository branches: {e}")
            traceback.print_exc()
            return BranchSyncResult.create_failure(str(e))
    
    def sync_repository_permissions(self, repository_id: int = None) -> SyncResult:
        """同步仓库权限信息"""
        try:
            if repository_id:
                try:
                    project = self.gl.projects.get(repository_id)
                    repositories = [project]
                except gitlab.exceptions.GitlabGetError:
                    return SyncResult.create_failure(
                        f'Repository {repository_id} not found'
                    )
            else:
                # 从数据库获取已同步的仓库
                repo_ids = self.db_service.get_all_repository_ids()
                if not repo_ids:
                    return SyncResult.create_failure(
                        'No repositories found in database. Please sync repositories first.'
                    )
                
                repositories = []
                for repo_id_obj in repo_ids:
                    try:
                        project = self.gl.projects.get(repo_id_obj.id)
                        repositories.append(project)
                    except Exception as e:
                        print(f"Error getting project {repo_id_obj.id}: {e}")
                        continue
            
            print(f"Starting permissions sync for {len(repositories)} repositories...")
            
            total_synced = 0
            processed_repos = 0
            
            for project in repositories:
                try:
                    print(f"Processing permissions for repository {project.id} ({project.name})")
                    
                    # 获取项目成员
                    members = project.members_all.list(all=True)
                    print(f"Found {len(members)} members for repository {project.id}")
                    
                    permission_data = []
                    
                    for member in members:
                        access_level_name = self._get_access_level_name(member.access_level)
                        permission_dto = GitlabPermissionData.from_model(member, access_level_name)  # 修正：使用 from_model
                        permission_data.append(permission_dto.to_dict())
                    
                    sync_result = self.db_service.sync_repository_permissions(project.id, permission_data)
                    if sync_result.success:
                        total_synced += sync_result.count  # 修正：使用 count 属性
                        processed_repos += 1
                        print(f"Synced {sync_result.count} permissions for repository {project.id}")
                    
                except Exception as e:
                    print(f"Error syncing permissions for repository {project.id}: {e}")
                    traceback.print_exc()
                    continue
            
            print(f"Successfully synced {total_synced} permissions for {processed_repos} repositories")
            return SyncResult.create_success(
                total_synced, 
                len(repositories)
            )
            
        except Exception as e:
            print(f"Error syncing repository permissions: {e}")
            traceback.print_exc()
            return SyncResult.create_failure(str(e))
    
    def _get_access_level_name(self, access_level: int) -> str:
        """将访问级别数字转换为名称"""
        level_names = {
            10: 'Guest',
            20: 'Reporter',
            30: 'Developer',
            40: 'Maintainer',
            50: 'Owner'
        }
        return level_names.get(access_level, 'Unknown')
    
    def sync_all(self) -> AllSyncResult:
        """同步所有数据并生成清理汇总"""
        repositories = self.sync_repositories()
        groups = self.sync_groups()
        branches = self.sync_repository_branches()
        permissions = self.sync_repository_permissions()
        
        # 同步完成后生成清理汇总
        if branches.success:
            print("Generating branch cleanup summary...")
            from services.cleanup_history_service import CleanupHistoryService
            cleanup_service = CleanupHistoryService()
            summary_result = cleanup_service.generate_daily_cleanup_summary()
            
            if summary_result['success']:
                print("✓ Cleanup summary generated successfully")
            else:
                print(f"✗ Failed to generate cleanup summary: {summary_result['error']}")
        
        return AllSyncResult.create_from_results(
            repositories, groups, branches, permissions
        )
    
    def _analyze_repository_branches(self, repository_id: int):
        """分析仓库分支并更新规则匹配结果"""
        try:
            # 使用查询服务获取分支和规则
            data = self.query_service.get_repository_branches_and_rules(repository_id)
            branches = data['branches']
            rules = data['rules']
            
            with get_db_session() as db:
                for branch in branches:
                    # 使用 export_service 中的规则匹配逻辑
                    rule_result = self._calculate_branch_rules(branch, rules)
                    
                    # 重新获取分支对象（因为 branch 来自不同的 session）
                    db_branch = db.query(GitlabRepositoryBranch).filter(
                        GitlabRepositoryBranch.id == branch.id
                    ).first()
                    
                    if db_branch:
                        # 更新数据库字段
                        db_branch.branch_type = rule_result['branch_type']
                        db_branch.is_deletable = rule_result['is_deletable']
                        db_branch.matched_rule_id = rule_result.get('matched_rule_id')
                        db_branch.retention_deadline = rule_result['retention_deadline']
                    branch.deletion_reason = rule_result['deletion_reason']
                
                db.commit()
                print(f"Updated rule analysis for {len(branches)} branches in repository {repository_id}")
                
        except Exception as e:
            print(f"Error analyzing branches for repository {repository_id}: {e}")

    def _calculate_branch_rules(self, branch: GitlabRepositoryBranch, rules: list) -> Dict[str, Any]:
        """计算分支规则（复用 export_service 的逻辑）"""
        from services.export_service import ExportService
        export_service = ExportService()
        
        # 模拟数据库会话上下文
        with get_db_session() as db:
            result = export_service._apply_branch_rules(branch, db)
            
            # 添加 matched_rule_id
            if result.get('matched_rule_name'):
                for rule in rules:
                    if rule.rule_name == result['matched_rule_name']:
                        result['matched_rule_id'] = rule.id
                        break
            
            return result

    def create_tag_and_record(self, tag_dto: TagCreateDTO) -> Dict[str, Any]:
        """在指定仓库的分支上创建tag，并写入GitlabTagRelation表
        
        Args:
            tag_dto: Tag 创建数据传输对象
            
        Returns:
            {'success': bool, 'message': str, 'error': str}
        """
        repo_field_map = {
            'apk': 'apk_tag',
            'nena': 'nena_tag',
            'ocserver': 'ocserver_tag',
            'clientcpp': 'clientcpp_tag',
            'onecloudserver': 'onecloudserver_tag',
            'onecloudclient': 'onecloudclient_tag',
            'otaweb': 'otaweb_tag',
            'nmasdkapi': 'nmasdkapi_tag',
            'nmasdkbl': 'nmasdkbl_tag',
            'devops': 'devops_tag',
            'nmasdkhmi': 'nmasdkhmi_tag',
        }

        # 1. 验证仓库信息
        repo_obj = self.query_service.get_repository_by_id(tag_dto.repository_id)
        if not repo_obj:
            return {"success": False, "error": f"数据库未找到仓库ID: {tag_dto.repository_id}"}
        
        repo_name = repo_obj.name.lower()
        if repo_name not in repo_field_map:
            return {"success": False, "error": f"仓库 '{repo_name}' 不在支持的仓库列表中"}
        
        field_name = repo_field_map[repo_name]
        project_id = repo_obj.id

        # 2. 调用 GitLab API 创建 tag
        tag_created = False
        try:
            project = self.gl.projects.get(project_id)
            tag = project.tags.create({
                'tag_name': tag_dto.tag_name,
                'ref': tag_dto.branch
            })
            tag_created = True
            logger.info(f"Created tag '{tag_dto.tag_name}' in GitLab project {project_id}")
        except Exception as e:
            error_msg = str(e)
            # 检查是否是"tag already exists"错误
            if "already exists" in error_msg.lower():
                logger.info(f"Tag '{tag_dto.tag_name}' already exists in GitLab, will record to database anyway")
            else:
                logger.error(f"Failed to create tag in GitLab: {e}")
                return {"success": False, "error": f"GitLab创建tag失败: {e}"}

        # 3. 调用 DatabaseService 写入数据库（职责分离）
        db_result = self.db_service.create_or_update_tag_relation(
            field_name=field_name,
            tag_name=tag_dto.tag_name,
            user=tag_dto.user,
            description=tag_dto.description
        )
        
        if not db_result['success']:
            return {"success": False, "error": f"数据库写入失败: {db_result.get('error')}"}
        
        # 4. 返回结果
        action = db_result.get('action', 'unknown')
        if tag_created:
            return {
                "success": True, 
                "message": f"Tag '{tag_dto.tag_name}' 在仓库 '{repo_obj.name}' 创建并记录成功"
            }
        else:
            return {
                "success": True, 
                "message": f"Tag '{tag_dto.tag_name}' 已存在，记录已{action}"
            }

    def parse_gitmodules(self, project_id: int, ref: str, 
                         filter_external: bool = True, 
                         normalize_url: bool = True) -> List[Dict[str, str]]:
        """解析项目的 .gitmodules 文件，返回子模块列表。
        
        Args:
            project_id: GitLab 项目 ID
            ref: 分支名或 tag name
            filter_external: 是否过滤 external/ 和 bin/ 开头的子模块
            normalize_url: 是否标准化 URL（移除 ../、协议、域名等）
        
        Returns:
            子模块列表，每个元素为 dict: {'path': ..., 'url': ..., 'branch': ...}
            如果读取失败或没有子模块，返回空列表
        """
        try:
            project = self.gl.projects.get(project_id)
            f = project.files.get(file_path='.gitmodules', ref=ref)
            content = f.decode().decode('utf-8')
        except Exception as e:
            logger.info(f'Cannot read .gitmodules from project {project_id} at ref {ref}: {e}')
            return []
        
        # 解析 .gitmodules 文件
        submodules = []
        current = {}
        
        for line in content.splitlines():
            line = line.strip()
            
            # 跳过空行
            if not line:
                continue
            
            # 新的子模块块
            if line.startswith('[submodule'):
                # 保存上一个子模块
                if current.get('path') and current.get('url'):
                    if self._should_include_submodule(current, filter_external):
                        submodules.append(current)
                current = {}
                continue
            
            # 解析键值对
            if '=' in line:
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip()
                
                if k == 'path':
                    current['path'] = v
                elif k == 'url':
                    # URL 标准化
                    if normalize_url:
                        v = self._normalize_submodule_url(v)
                    current['url'] = v
                elif k == 'branch':
                    current['branch'] = v
        
        # 保存最后一个子模块
        if current.get('path') and current.get('url'):
            if self._should_include_submodule(current, filter_external):
                submodules.append(current)
        
        logger.info(f'Parsed {len(submodules)} submodules from project {project_id} at ref {ref}')
        return submodules
    
    def _normalize_submodule_url(self, url: str) -> str:
        """标准化子模块 URL。
        移除 ../、协议、域名等，返回相对路径或项目路径。
        """
        normalized = url
        
        # 移除协议和域名（如果存在）
        if '://' in normalized:
            normalized = normalized.split('://', 1)[1]
            # 如果包含域名，删除到第一个 '/' 之前的内容
            if '/' in normalized and '.' in normalized.split('/')[0]:
                normalized = '/'.join(normalized.split('/')[1:])
        
        # 移除前导的 ../
        while normalized.startswith('../'):
            normalized = normalized[3:]
        
        # 移除 .git 后缀（使用 removesuffix 或条件判断，避免 rstrip 的问题）
        if normalized.endswith('.git'):
            normalized = normalized[:-4]  # 移除最后 4 个字符 '.git'
        
        normalized = normalized.strip('/')
        
        return normalized
    
    def _should_include_submodule(self, submodule: Dict[str, str], filter_external: bool) -> bool:
        """判断是否应该包含该子模块。
        
        Args:
            submodule: 子模块信息字典
            filter_external: 是否过滤 external/ 和 bin/ 开头的子模块
        
        Returns:
            True 表示应该包含，False 表示应该过滤掉
        """
        if not filter_external:
            return True
        
        url = submodule.get('url', '')
        # 过滤 external/ 和 bin/ 开头的子模块
        if url.startswith('external/') or url.startswith('bin/'):
            return False
        
        return True
    
    def _check_ref_exists(self, project: Any, ref_name: str, ref_type: str = 'auto') -> Dict[str, Any]:
        """检查项目中是否存在指定的引用（分支或标签）。
        
        Args:
            project: GitLab项目对象
            ref_name: 引用名称
            ref_type: 'branch', 'tag', 或 'auto' (自动检测)
            
        Returns:
            {
                'exists': bool,
                'type': 'branch'|'tag'|None,  # 存在时返回类型
                'ref': ref对象或None
            }
        """
        result = {'exists': False, 'type': None, 'ref': None}
        
        if ref_type in ('auto', 'tag'):
            try:
                tag = project.tags.get(ref_name)
                result['exists'] = True
                result['type'] = 'tag'
                result['ref'] = tag
                return result
            except Exception:
                if ref_type == 'tag':
                    return result
        
        if ref_type in ('auto', 'branch'):
            try:
                branch = project.branches.get(ref_name)
                result['exists'] = True
                result['type'] = 'branch'
                result['ref'] = branch
                return result
            except Exception:
                pass
        
        return result
    
    def _resolve_commit_sha(self, project: Any, ref: str, try_tags: bool = True) -> Optional[str]:
        """从引用名称解析为commit SHA。
        
        Args:
            project: GitLab项目对象
            ref: 引用名称 (branch/tag/commit)
            try_tags: 如果branch查询失败，是否尝试查询tag
            
        Returns:
            commit SHA字符串，失败返回None
        """
        if not ref:
            return None
        
        # 如果已经是SHA格式 (40位十六进制)
        if len(ref) == 40 and ref.isalnum():
            return ref
        
        # 尝试从branch/tag获取commit
        try:
            commits = project.commits.list(ref_name=ref, per_page=1, get_all=False)
            if commits:
                return commits[0].id
        except Exception:
            pass
        
        # 如果需要，尝试从tag获取
        if try_tags:
            try:
                tags = project.tags.list(search=ref, per_page=1, get_all=False)
                if tags and len(tags) > 0:
                    tag = tags[0]
                    # tag.commit可能是dict或对象
                    if isinstance(tag.commit, dict):
                        return tag.commit.get('id')
                    else:
                        return getattr(tag.commit, 'id', None)
            except Exception:
                pass
        
        return None
    
    def _record_branch_creation(self, project_id: int, branch_name: str, 
                               source_ref: str, source_commit: Optional[str],
                               status: str, message: Optional[str] = None,
                               jira_ticket: Optional[str] = None, 
                               created_by: Optional[str] = None,
                               context: str = 'branch') -> bool:
        """记录分支创建到数据库。
        
        Args:
            project_id: 项目ID
            branch_name: 分支名称
            source_ref: 源引用
            source_commit: 源commit SHA
            status: 状态 ('created', 'already_exists', 'failed')
            message: 错误消息（可选）
            jira_ticket: JIRA工单号（可选）
            created_by: 创建人（可选）
            context: 上下文描述（用于日志）
            
        Returns:
            是否记录成功
        """
        try:
            result = self.db_service.create_branch_creation_record(
                project_id=project_id,
                branch_name=branch_name,
                source_ref=source_ref,
                source_commit=source_commit or '',
                status=status or 'unknown',
                message=message,
                jira_ticket=jira_ticket,
                created_by=created_by
            )
            if result['success']:
                logger.debug(f"Recorded {context} branch creation for project {project_id}: {branch_name} ({status})")
                return True
            else:
                logger.warning(f"Failed to record {context} branch creation: {result.get('error')}")
                return False
        except Exception:
            logger.exception(f'Failed to record {context} branch creation for project {project_id}')
            return False
    
    def _find_gitlab_project(self, project_path: str, fallback_name: str = None) -> Optional[Any]:
        """查找 GitLab 项目对象，优先使用数据库缓存，失败时回退到 GitLab API。
        
        Args:
            project_path: 项目路径（如 'hb_common/na_common' 或 'funit/nds'）
            fallback_name: 回退时用于搜索的项目名（如 'na_common'），可选
        
        Returns:
            GitLab 项目对象，如果未找到返回 None
        """
        # 步骤 1: 优先从数据库精确查找（最快，~2ms）
        # 使用精确匹配避免误匹配（如 'funit/nds' 不应匹配到 'internal_share/nds_format'）
        repo_info = self.query_service.find_repository_by_name(project_path, use_fuzzy=False)
        
        if repo_info:
            # repo_info 是字典: {'id': int, 'name': str, 'path': str}
            repo_id = repo_info['id']
            try:
                # 从数据库找到了，使用 GitLab API 获取完整项目对象
                project = self.gl.projects.get(repo_id)
                logger.debug(f"Found project '{project_path}' in database with id {repo_id}")
                return project
            except Exception as e:
                logger.warning(f"Found project '{project_path}' in database (id={repo_id})")
        
        # 步骤 2: 数据库未找到或API失败，回退到 GitLab API 路径查询（~200ms）
        try:
            project = self.gl.projects.get(project_path)
            logger.debug(f"Found project '{project_path}' via GitLab API path query")
            return project
        except Exception as e:
            logger.debug(f"GitLab API path query failed for '{project_path}': {e}")
        
        # 步骤 3: 如果提供了回退名称，尝试按名称搜索（~300ms）
        if fallback_name:
            try:
                candidates = self.gl.projects.list(search=fallback_name, all=True)
                for candidate in candidates:
                    # 优先精确路径匹配
                    if getattr(candidate, 'path_with_namespace', None) and candidate.path_with_namespace.endswith(project_path):
                        logger.debug(f"Found project '{project_path}' via GitLab API name search (exact match)")
                        return candidate
                    # 次选：名称匹配
                    if candidate.path == fallback_name or getattr(candidate, 'name', '') == fallback_name:
                        logger.debug(f"Found project '{project_path}' via GitLab API name search (name match)")
                        return candidate
            except Exception as e:
                logger.debug(f"GitLab API name search failed for '{fallback_name}': {e}")
        
        # 所有方法都失败了
        logger.warning(f"Project '{project_path}' not found in database or GitLab")
        return None
    
    def _resolve_submodule_project(self, submodule: Dict[str, str]) -> Optional[Any]:
        """从 .gitmodules 子模块信息解析 GitLab 项目对象
        
        Args:
            submodule: 子模块信息字典，包含 'path', 'url', 'branch' 等字段
            
        Returns:
            GitLab 项目对象，如果未找到返回 None
        """
        path = submodule.get('path')
        if not path:
            logger.warning("Submodule missing 'path' field")
            return None
        
        # 直接使用 path 字段作为项目路径（如 'funit/mapviewpro'）
        project_path = path
        
        # 提取项目名称（用于回退查找）
        parts = project_path.split('/')
        if len(parts) < 1:
            logger.warning(f"Invalid submodule path: '{path}'")
            return None
        
        fallback_name = parts[-1]  # 最后一部分是项目名
        
        # 使用统一的项目查找方法（优先数据库，回退到API）
        return self._find_gitlab_project(project_path, fallback_name=fallback_name)

    def get_submodule_commit(self, parent_project_id: int, submodule_path: str, ref: str = 'master') -> Optional[str]:
        """获取主库中记录的 submodule commit id。
        使用 GitLab API 的 repository_tree 方法读取，这是最简单可靠的方法。
        返回 commit sha 或 None。
        """
        try:
            project = self.gl.projects.get(parent_project_id)
            logger.info(f"Getting submodule '{submodule_path}' commit from project {parent_project_id} at ref '{ref}'")
            
            # 方法1: 直接查询子模块路径
            try:
                tree_items = project.repository_tree(path=submodule_path, ref=ref, per_page=1)
                logger.debug(f"Direct path query returned {len(tree_items)} items")
                
                if tree_items and len(tree_items) > 0:
                    item = tree_items[0]
                    # 检查 mode 是否为 160000（gitlink）
                    if item.get('mode') == '160000' or item.get('type') == 'commit':
                        sha = item.get('id')
                        if sha:
                            logger.info(f"Successfully got submodule commit from direct query: {sha[:8]}")
                            return sha
            except Exception as e:
                logger.debug(f"Direct path query failed: {e}")
            
            # 方法2: 查询父目录，然后找到对应的子模块
            parent_dir = os.path.dirname(submodule_path)
            submodule_name = os.path.basename(submodule_path)
            
            try:
                logger.debug(f"Trying parent directory: '{parent_dir}', looking for '{submodule_name}'")
                tree_items = project.repository_tree(path=parent_dir or '', ref=ref, per_page=100)
                logger.debug(f"Parent directory query returned {len(tree_items)} items")
                
                for item in tree_items:
                    # 匹配路径或名称
                    item_path = item.get('path', '')
                    item_name = item.get('name', '')
                    
                    if item_path == submodule_path or item_name == submodule_name:
                        # 检查是否是 submodule (mode 160000)
                        if item.get('mode') == '160000' or item.get('type') == 'commit':
                            sha = item.get('id')
                            if sha:
                                logger.info(f"Successfully got submodule commit from parent dir query: {sha[:8]}")
                                return sha
                            else:
                                logger.warning(f"Found matching item but no id field: {item}")
                
                logger.warning(f"Submodule '{submodule_path}' not found in parent directory listing")
                
            except Exception as e:
                logger.warning(f"Parent directory query failed for ref '{ref}': {e}")
            
            # 都失败了
            logger.warning(f"Failed to get submodule commit for '{submodule_path}' at ref '{ref}'")
            return None
            
        except Exception as e:
            logger.error(f"Error getting submodule commit: {e}", exc_info=True)
            return None

    def create_branch_with_submodules(self, group_name: str, project_name: str, project_id: int, 
                                     new_branch_name: str, ref_branch: str, jira_ticket: str = None, 
                                     created_by: str = None) -> Dict[str, Any]:
        """在主仓库创建分支，并尝试在关联的子模块仓库创建同名分支。
        子模块创建分支的优先策略：
          1) 如果子仓库存在同名 tag 或 branch，则直接用它作为 source ref；
          2) 否则尝试读取主仓库在 ref_branch 中记录的 submodule commit id，并用该 sha 创建分支；
          3) 最后回退到将 ref_branch 的 'own' 替换为 'other' 的策略（保持和现有脚本一致）。
        返回创建结果摘要。
        """
        result = {'created_in_parent': False, 'parent_created': None, 'submodules': []}
        try:
            project = self.gl.projects.get(project_id)
        except Exception as e:
            return {'error': f'Failed to get parent project: {e}'}

        # 创建父仓库分支（若不存在）
        parent_status = None
        parent_message = None
        try:
            try:
                project.branches.get(new_branch_name)
                result['created_in_parent'] = False
                result['parent_created'] = 'already_exists'
                parent_status = 'already_exists'
            except gitlab.exceptions.GitlabGetError:
                project.branches.create({'branch': new_branch_name, 'ref': ref_branch})
                result['created_in_parent'] = True
                result['parent_created'] = 'created'
                parent_status = 'created'
        except Exception as e:
            error_str = str(e)
            result['parent_created'] = f'failed: {e}'
            parent_status = 'failed'
            parent_message = error_str  # 将详细错误信息保存到 message

        # Persist parent branch creation attempt to DB
        source_ref = ref_branch
        source_commit = self._resolve_commit_sha(project, ref_branch, try_tags=False)

        # if already exists, get its commit
        if result.get('parent_created') == 'already_exists':
            try:
                br = project.branches.get(new_branch_name)
                source_commit = br.commit['id'] if br and br.commit else source_commit
            except Exception:
                pass

        # 使用统一方法记录分支创建
        self._record_branch_creation(
            project_id, new_branch_name, source_ref, source_commit,
            parent_status, parent_message, jira_ticket, created_by, 'parent'
        )

        # 读取并解析 .gitmodules（过滤 external/ 和 bin/ 子模块）
        submodule_info = self.parse_gitmodules(
            project_id=project_id, 
            ref=ref_branch, 
            filter_external=True,
            normalize_url=True
        )
        
        # 如果没有找到任何子模块
        if not submodule_info:
            logger.info(f'Project {project_id} has .gitmodules but no valid submodules (all filtered out)')
            result['has_submodules'] = False
            result['submodules_message'] = '.gitmodules found but contains no valid submodules'
            return result
        
        # 有子模块需要处理
        logger.info(f'Found {len(submodule_info)} submodules in project {project_id}')
        result['has_submodules'] = True

        # 处理每个子模块
        for sm in submodule_info:
            submodule_path = sm['path']  # .gitmodules 中的 path 字段，如 'funit/mapviewpro'
            url = sm.get('url', '')  # 保留用于日志记录
            project_path = submodule_path  # 用于结果记录

            sub_result = {'url': url, 'path': submodule_path, 'project': project_path}
            
            # 使用统一的项目解析方法
            sub_proj = self._resolve_submodule_project(sm)

            if not sub_proj:
                sub_result['status'] = 'not_found'
                result['submodules'].append(sub_result)
                continue

            # 根据 .gitmodules 中的 branch 字段判断是否需要为该子库创建分支
            # branch = "." 表示跟随主库分支（需要创建）
            # branch = "uranus" 或其他固定分支名表示子库固定使用该分支（不需要创建新分支）
            submodule_branch_config = sm.get('branch', '.')  # 默认为 "." 表示跟随主库
            
            # 如果配置了固定分支名（不是 "."），则跳过该子模块的分支创建
            if submodule_branch_config != '.':
                sub_result['status'] = 'skipped'
                sub_result['reason'] = f'submodule configured with fixed branch: {submodule_branch_config}'
                sub_result['fixed_branch'] = submodule_branch_config
                result['submodules'].append(sub_result)
                logger.info(f"Skipping submodule {submodule_path} - configured with fixed branch '{submodule_branch_config}'")
                continue
            
            # 决定用于创建分支的 ref
            chosen_ref = None
            try:
                # 首先判断 ref_branch 在主库中是分支还是 tag
                ref_check = self._check_ref_exists(project, ref_branch, ref_type='auto')
                is_tag_in_parent = (ref_check['type'] == 'tag')
                is_branch_in_parent = (ref_check['type'] == 'branch')
                
                # 策略1: 如果 ref_branch 是分支名，主库和子库都使用该分支名创建新分支
                if is_branch_in_parent:
                    sub_branch_check = self._check_ref_exists(sub_proj, ref_branch, ref_type='branch')
                    if sub_branch_check['exists']:
                        chosen_ref = ref_branch
                        sub_result['ref_source'] = 'same_branch_name'
                        logger.info(f"Submodule {submodule_path}: found same branch name '{ref_branch}'")
                    else:
                        # 子库没有同名分支，直接跳到使用 commit id（策略3）
                        logger.info(f"Submodule {submodule_path}: branch '{ref_branch}' not found, will try commit id")
                
                # 策略2: 如果 ref_branch 是 tag name，子库转换 own/release -> other/release 后基于 tag 创建新分支
                if not chosen_ref and is_tag_in_parent:
                    # 主库基于 own/release tag，子库应该基于 other/release tag
                    converted_ref = ref_branch.replace('own/', 'other/')
                    converted_tag_check = self._check_ref_exists(sub_proj, converted_ref, ref_type='tag')
                    if converted_tag_check['exists']:
                        chosen_ref = converted_ref
                        sub_result['ref_source'] = 'converted_tag_own_to_other'
                        logger.info(f"Submodule {submodule_path}: found converted tag '{converted_ref}'")
                    else:
                        # 转换后的 tag 不存在，直接跳到使用 commit id（策略3）
                        logger.info(f"Submodule {submodule_path}: converted tag '{converted_ref}' not found, will try commit id")
                
                # 策略3: 如果分支/tag 都不存在，使用主库 .gitmodules 中记录的精确 commit id
                if not chosen_ref:
                    sha = self.get_submodule_commit(project_id, submodule_path, ref_branch)
                    if sha:
                        chosen_ref = sha
                        sub_result['ref_source'] = 'submodule_commit_from_gitmodules'
                        logger.info(f"Submodule {submodule_path}: using commit id from .gitmodules: {sha[:8]}")
                
                # 策略4: 最后的兜底 - 使用子库的默认分支
                if not chosen_ref:
                    chosen_ref = getattr(sub_proj, 'default_branch', 'master')
                    sub_result['ref_source'] = 'default_branch'
                    logger.warning(f"Submodule {submodule_path}: falling back to default branch '{chosen_ref}'")

                # 创建分支（若不存在）
                branch_status = None
                branch_message = None  # 用于保存详细错误信息
                try:
                    try:
                        sub_proj.branches.get(new_branch_name)
                        sub_result['status'] = 'already_exists'
                        sub_result['used_ref'] = chosen_ref
                        branch_status = 'already_exists'
                    except gitlab.exceptions.GitlabGetError:
                        sub_proj.branches.create({'branch': new_branch_name, 'ref': chosen_ref})
                        sub_result['status'] = 'created'
                        sub_result['used_ref'] = chosen_ref
                        branch_status = 'created'
                except Exception as e:
                    error_str = str(e)
                    sub_result['status'] = f'create_failed: {e}'
                    branch_status = 'failed'
                    branch_message = error_str  # 保存详细错误信息

                # Persist submodule branch creation to DB
                # 使用统一方法解析commit SHA并记录分支创建
                source_commit = self._resolve_commit_sha(sub_proj, chosen_ref, try_tags=False)
                self._record_branch_creation(
                    sub_proj.id, new_branch_name, chosen_ref, source_commit,
                    branch_status, branch_message, jira_ticket, created_by, 'submodule'
                )

            except Exception as e:
                sub_result['status'] = f'error: {e}'

            result['submodules'].append(sub_result)

        return result

    def update_all_submodules_from_gitmodules(self, parent_project_id: int, parent_ref: str = 'master', target_branch: Optional[str] = None) -> Dict[str, Any]:
        """Read `.gitmodules` from parent (at parent_ref), for each submodule find the subproject and
        update the parent repository's gitlinks to point to the latest commit on the same ref (or default branch),
        committing all changes in one new branch and pushing it.

        This avoids cloning/downloading full submodule working trees. It requires `git` available on the host
        and that the caller has push permissions to the parent repository (or will push to a branch).

        Returns a dict with operation status and per-submodule results.
        """
        result = {'parent_project_id': parent_project_id, 'updated': False, 'branch': None, 'submodules': []}

        try:
            parent = self.gl.projects.get(parent_project_id)
        except Exception as e:
            return {'error': f'Cannot get parent project: {e}'}

        # 读取并解析 .gitmodules（不过滤子模块，需要更新所有）
        submodules = self.parse_gitmodules(
            project_id=parent_project_id,
            ref=parent_ref,
            filter_external=False,
            normalize_url=True
        )
        
        if not submodules:
            return {'error': 'No submodules found in .gitmodules'}

        # Determine branch name to push
        import time
        timestamp = int(time.time())
        if not target_branch:
            target_branch = f'update-submodules/{timestamp}'
        result['branch'] = target_branch

        # For each submodule, resolve project and get target SHA
        sub_results = []
        for sm in submodules:
            smr = {'path': sm.get('path'), 'url': sm.get('url'), 'resolved_project': None, 'sha': None, 'error': None}
            
            if not sm.get('path'):
                smr['error'] = 'missing path'
                sub_results.append(smr)
                continue

            # 使用统一的项目解析方法
            subproj = self._resolve_submodule_project(sm)

            if not subproj:
                smr['error'] = 'cannot_resolve_subproject'
                sub_results.append(smr)
                continue

            smr['resolved_project'] = getattr(subproj, 'path_with_namespace', getattr(subproj, 'id', None))

            # decide which ref to use for submodule: prefer the submodule's configured branch, else parent_ref, else subproj.default_branch
            candidate_refs = []
            if sm.get('branch'):
                candidate_refs.append(sm.get('branch'))
            candidate_refs.append(parent_ref)
            if getattr(subproj, 'default_branch', None):
                candidate_refs.append(subproj.default_branch)

            # 使用统一方法尝试解析每个候选 ref 的 commit SHA
            sha = None
            for r in candidate_refs:
                if not r:
                    continue
                sha = self._resolve_commit_sha(subproj, r, try_tags=True)
                if sha:
                    break

            if not sha:
                smr['error'] = 'cannot_resolve_sha'
                sub_results.append(smr)
                continue

            smr['sha'] = sha
            sub_results.append(smr)

        result['submodules'] = sub_results

        # If no submodule SHAs resolved, abort
        if not any(s.get('sha') for s in sub_results):
            result['error'] = 'no_submodule_shas_resolved'
            return result

        # Now perform lightweight git update: init tmp repo, fetch parent_ref, checkout branch, update-index for each submodule, commit and push
        tmpdir = tempfile.mkdtemp(prefix='update_submods_')
        try:
            subprocess.check_call(['git', 'init'], cwd=tmpdir)
            subprocess.check_call(['git', 'remote', 'add', 'origin', getattr(parent, 'http_url_to_repo', parent.web_url)], cwd=tmpdir)
            # fetch parent ref
            subprocess.check_call(['git', 'fetch', '--depth', '1', 'origin', parent_ref], cwd=tmpdir)
            # create target branch from fetched head
            subprocess.check_call(['git', 'checkout', '-b', target_branch, 'FETCH_HEAD'], cwd=tmpdir)

            # apply updates
            any_updated = False
            for s in sub_results:
                if s.get('sha') and s.get('path'):
                    any_updated = True
                    subprocess.check_call(['git', 'update-index', '--add', '--cacheinfo', f'160000,{s["sha"]},{s["path"]}'], cwd=tmpdir)

            if not any_updated:
                result['error'] = 'no_updates_applied'
                return result

            # commit
            subprocess.check_call(['git', 'commit', '-m', f'Update submodule pointers ({len([x for x in sub_results if x.get("sha")])})'], cwd=tmpdir)
            # push
            subprocess.check_call(['git', 'push', 'origin', f'HEAD:refs/heads/{target_branch}'], cwd=tmpdir)

            result['updated'] = True
            
            # 调用 DatabaseService 持久化记录（成功）
            db_result = self.db_service.create_submodule_update_record(
                parent_project_id=parent_project_id,
                target_branch=target_branch,
                status='success',
                details=result.get('submodules')
            )
            if not db_result['success']:
                logger.warning(f"Failed to write submodule update record to DB: {db_result.get('error')}")

            return result
        except subprocess.CalledProcessError as e:
            result['error'] = f'git operation failed: {e}'
            
            # 调用 DatabaseService 持久化记录（失败）
            db_result = self.db_service.create_submodule_update_record(
                parent_project_id=parent_project_id,
                target_branch=target_branch,
                status='failure',
                details=result.get('submodules')
            )
            if not db_result['success']:
                logger.warning(f"Failed to write failed submodule update record to DB: {db_result.get('error')}")

            return result
        finally:
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass
    
    def generate_branch_summaries(self, force_refresh: bool = False) -> dict:
        """为所有仓库生成分支汇总统计"""
        from database.models import GitlabBranchSummary
        
        try:
            # 如果强制刷新，先清空旧数据
            if force_refresh:
                result = self.db_service.delete_all_branch_summaries()
                if result['success']:
                    logger.info(f"已清空 {result['count']} 条分支汇总数据")
            
            # 获取所有仓库
            repo_ids = self.db_service.get_all_repository_ids()
            logger.info(f"开始为 {len(repo_ids)} 个仓库生成分支汇总")
            
            success_count = 0
            error_count = 0
            
            for repo_id_obj in repo_ids:
                try:
                    result = self.generate_repository_summary(repo_id_obj.id)
                    if result['success']:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"生成仓库 {repo_id_obj.id} 的汇总失败: {e}")
            
            return {
                'success': True,
                'total_repositories': len(repo_ids),
                'success_count': success_count,
                'error_count': error_count,
                'message': f'已为 {success_count}/{len(repo_ids)} 个仓库生成分支汇总'
            }
            
        except Exception as e:
            logger.exception("生成分支汇总失败")
            return {
                'success': False,
                'error': str(e),
                'message': '生成分支汇总失败'
            }
    
    def generate_repository_summary(self, repository_id: int) -> dict:
        """为单个仓库生成分支汇总统计"""
        from database.models import GitlabRepositoryBranch, GitlabBranchSummary, GitlabRepository
        
        try:
            # 在同一个 session 中获取仓库和分支信息
            with get_db_session() as db:
                # 获取仓库信息
                repo = db.query(GitlabRepository).filter_by(id=repository_id).first()
                if not repo:
                    return {
                        'success': False,
                        'error': f'仓库 {repository_id} 不存在'
                    }
                
                # 获取该仓库的所有分支
                branches = db.query(GitlabRepositoryBranch).filter_by(
                    repository_id=repository_id
                ).all()
                
                # 计算统计数据（传递 repo 的属性值，而不是 repo 对象）
                summary_data = self._calculate_branch_statistics(
                    repo_id=repo.id,
                    repo_name=repo.name,
                    default_branch=repo.default_branch,
                    branches=branches
                )
            
            # 保存到数据库（在新的 session 中）
            save_result = self.db_service.save_branch_summary(summary_data)
            
            if save_result['success']:
                return {
                    'success': True,
                    'message': f'已为仓库 {summary_data["repository_name"]} 生成分支汇总',
                    'data': summary_data
                }
            else:
                return save_result
                
        except Exception as e:
            logger.exception(f"生成仓库 {repository_id} 的分支汇总失败")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_branch_statistics(self, repo_id: int, repo_name: str, 
                                     default_branch: str, branches: list) -> dict:
        """计算分支统计数据（内部方法）"""
        from datetime import datetime
        
        now = datetime.now()
        
        # 基础统计
        total_branches = len(branches)
        protected_branches = sum(1 for b in branches if b.protected)
        deletable_branches = sum(1 for b in branches if b.is_deletable)
        
        # 按分支类型统计（使用分支名前缀匹配）
        feature_branches = sum(
            1 for b in branches 
            if b.branch_name and b.branch_name.lower().startswith('feature')
        )
        develop_branches = sum(
            1 for b in branches 
            if b.branch_name and b.branch_name.lower().startswith('dev')
        )
        release_branches = sum(
            1 for b in branches 
            if b.branch_name and b.branch_name.lower().startswith('release')
        )
        hotfix_branches = sum(
            1 for b in branches 
            if b.branch_name and b.branch_name.lower().startswith('hotfix')
        )
        main_branches = sum(
            1 for b in branches 
            if b.branch_name and b.branch_name.lower() in ['main', 'master']
        )
        
        stabilization_branches = sum(
            1 for b in branches 
            if b.branch_name and b.branch_name.lower().startswith('stabilization')
        )
        
        # other 分支：总分支数 - 所有已分类的分支类型总数
        other_branches = total_branches - (
            feature_branches + develop_branches + release_branches + 
            hotfix_branches + main_branches + stabilization_branches
        )
        
        # 按活跃度统计
        active_30days = sum(
            1 for b in branches 
            if b.last_commit_date and (now - b.last_commit_date).days <= 30
        )
        active_90days = sum(
            1 for b in branches 
            if b.last_commit_date and (now - b.last_commit_date).days <= 90
        )
        inactive_180days = sum(
            1 for b in branches 
            if b.last_commit_date and (now - b.last_commit_date).days > 180
        )
        inactive_365days = sum(
            1 for b in branches 
            if b.last_commit_date and (now - b.last_commit_date).days > 365
        )
        
        # 最新和最旧分支
        latest_branch_name = None
        latest_branch_date = None
        oldest_branch_name = None
        oldest_branch_date = None
        
        if branches:
            branches_with_date = [b for b in branches if b.last_commit_date]
            if branches_with_date:
                latest_branch = max(branches_with_date, key=lambda b: b.last_commit_date)
                latest_branch_name = latest_branch.branch_name
                latest_branch_date = latest_branch.last_commit_date
                
                oldest_branch = min(branches_with_date, key=lambda b: b.last_commit_date)
                oldest_branch_name = oldest_branch.branch_name
                oldest_branch_date = oldest_branch.last_commit_date
        
        # 默认分支信息
        default_branch_commit = None
        default_branch_last_commit_date = None
        
        if default_branch:
            default_branch_obj = next(
                (b for b in branches if b.branch_name == default_branch), 
                None
            )
            if default_branch_obj:
                default_branch_commit = default_branch_obj.commit_id
                default_branch_last_commit_date = default_branch_obj.last_commit_date
        
        return {
            'repository_id': repo_id,
            'repository_name': repo_name,
            'total_branches': total_branches,
            'protected_branches': protected_branches,
            'deletable_branches': deletable_branches,
            'feature_branches': feature_branches,
            'develop_branches': develop_branches,
            'release_branches': release_branches,
            'hotfix_branches': hotfix_branches,
            'main_branches': main_branches,
            'stabilization_branches': stabilization_branches,
            'other_branches': other_branches,
            'active_30days': active_30days,
            'active_90days': active_90days,
            'inactive_180days': inactive_180days,
            'inactive_365days': inactive_365days,
            'latest_branch_name': latest_branch_name,
            'latest_branch_date': latest_branch_date,
            'oldest_branch_name': oldest_branch_name,
            'oldest_branch_date': oldest_branch_date,
            'default_branch': default_branch,
            'default_branch_commit': default_branch_commit,
            'default_branch_last_commit_date': default_branch_last_commit_date,
            'last_sync_time': datetime.now(),
            'data_version': 1
        }
