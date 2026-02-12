from database.connection import get_db_session
from database.models import (
    GitlabApiAccessLog, LogImportStatus, GitlabRepository, 
    GitlabGroup, GitlabGroupMember, GitlabRepositoryBranch, 
    GitlabRepositoryPermission
)
from sqlalchemy import func, and_
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from dto.import_dto import ImportStatusSummary, ImportDetail, ImportResult
from dto.log_dto import ApiAccessLogData
from dto.sync_dto import SyncResult, RepositoryId
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseService:
    def __init__(self):
        pass
    
    def is_date_already_imported(self, target_date):
        """检查指定日期的数据是否已经导入"""
        try:
            with get_db_session() as db:
                status = db.query(LogImportStatus).filter(
                    LogImportStatus.import_date == target_date
                ).first()
                return status is not None
        except Exception as e:
            print(f"Error checking date: {e}")
            return False
    
    def record_import_status(self, import_date, record_count, log_file_path=None):
        """记录导入状态到状态表"""
        try:
            with get_db_session() as db:
                # 检查是否已存在该日期的记录
                existing = db.query(LogImportStatus).filter(
                    LogImportStatus.import_date == import_date
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.record_count += record_count
                    existing.import_time = datetime.now()
                    existing.log_file_path = log_file_path
                else:
                    # 创建新记录
                    import_status = LogImportStatus(
                        import_date=import_date,
                        record_count=record_count,
                        import_time=datetime.now(),
                        log_file_path=log_file_path,
                        is_complete=True
                    )
                    db.add(import_status)
                
                db.commit()
                print(f"Recorded import status for {import_date}: {record_count} records")
                
        except Exception as e:
            print(f"Error recording import status: {e}")
    
    def insert_logs(self, log_entries, log_file_path=None) -> ImportResult:
        """批量插入日志数据"""
        if not log_entries:
            return ImportResult.create_no_data()
        
        # 获取日志数据中的日期
        log_dates = set()
        for entry in log_entries:
            if 'access_time' in entry:
                if isinstance(entry['access_time'], datetime):
                    log_dates.add(entry['access_time'].date())
                elif isinstance(entry['access_time'], str):
                    try:
                        dt = datetime.fromisoformat(entry['access_time'].replace('Z', '+00:00'))
                        log_dates.add(dt.date())
                    except:
                        pass
        
        # 检查是否已经导入过这些日期的数据
        already_imported_dates = []
        for log_date in log_dates:
            if self.is_date_already_imported(log_date):
                already_imported_dates.append(log_date)
        
        if already_imported_dates:
            return ImportResult.create_already_imported(len(log_entries), already_imported_dates)
        
        # 执行插入
        try:
            with get_db_session() as db:
                inserted_count = 0
                for entry in log_entries:
                    try:
                        log_record = GitlabApiAccessLog(**entry)
                        db.add(log_record)
                        inserted_count += 1
                    except Exception as e:
                        print(f"Error inserting single record: {e}")
                        continue
                
                db.commit()
                
                # 记录每个日期的导入状态
                date_counts = {}
                for entry in log_entries:
                    if 'access_time' in entry:
                        if isinstance(entry['access_time'], datetime):
                            entry_date = entry['access_time'].date()
                        else:
                            try:
                                dt = datetime.fromisoformat(entry['access_time'].replace('Z', '+00:00'))
                                entry_date = dt.date()
                            except:
                                continue
                        
                        date_counts[entry_date] = date_counts.get(entry_date, 0) + 1
                
                # 记录到状态表
                for import_date, count in date_counts.items():
                    self.record_import_status(import_date, count, log_file_path)
                
                print(f"Successfully inserted {inserted_count} log entries")
                return ImportResult.create_success(inserted_count, len(log_entries), list(log_dates))
                
        except Exception as e:
            print(f"Error inserting logs: {e}")
            raise
    
    def get_import_status_summary(self) -> ImportStatusSummary:
        """从状态表获取导入状态摘要"""
        try:
            with get_db_session() as db:
                # 获取总体统计
                total_records = db.query(func.sum(LogImportStatus.record_count)).scalar() or 0
                
                # 获取日期范围
                date_range = db.query(
                    func.min(LogImportStatus.import_date).label('min_date'),
                    func.max(LogImportStatus.import_date).label('max_date'),
                    func.count(LogImportStatus.id).label('import_days')
                ).first()
                
                # 获取导入日期列表
                imported_dates = db.query(LogImportStatus.import_date).order_by(LogImportStatus.import_date).all()
                
                return ImportStatusSummary(
                    total_records=total_records,
                    min_date=date_range.min_date,
                    max_date=date_range.max_date,
                    import_days=date_range.import_days or 0,
                    imported_dates=[str(row.import_date) for row in imported_dates]
                )
                
        except Exception as e:
            print(f"Error getting import status: {e}")
            return ImportStatusSummary.create_empty()
    
    def get_import_details(self) -> List[ImportDetail]:
        """获取详细的导入状态"""
        try:
            with get_db_session() as db:
                details = db.query(LogImportStatus).order_by(LogImportStatus.import_date.desc()).all()
                
                return [
                    ImportDetail(
                        import_date=str(detail.import_date),
                        record_count=detail.record_count,
                        import_time=detail.import_time.isoformat(),
                        log_file_path=detail.log_file_path,
                        is_complete=detail.is_complete
                    )
                    for detail in details
                ]
                
        except Exception as e:
            print(f"Error getting import details: {e}")
            return []
    
    def get_logs(self, limit=100) -> List[ApiAccessLogData]:
        """获取日志数据"""
        try:
            with get_db_session() as db:
                logs = db.query(GitlabApiAccessLog).order_by(GitlabApiAccessLog.access_time.desc()).limit(limit).all()
                return [ApiAccessLogData.from_model(log) for log in logs]  # 修正：使用 from_model
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []
    
    def get_total_count(self):
        """从状态表获取总记录数"""
        try:
            with get_db_session() as db:
                return db.query(func.sum(LogImportStatus.record_count)).scalar() or 0
        except Exception as e:
            print(f"Error getting total count: {e}")
            return 0
    
    def sync_repositories(self, repositories: List[Dict]) -> SyncResult:
        """同步仓库数据到数据库"""
        try:
            with get_db_session() as db:
                synced_count = 0
                
                for repo_data in repositories:
                    try:
                        # 检查仓库是否已存在
                        existing_repo = db.query(GitlabRepository).filter(
                            GitlabRepository.id == repo_data['id']
                        ).first()
                        
                        if existing_repo:
                            # 更新现有仓库
                            existing_repo.name = repo_data.get('name', '')
                            existing_repo.name_with_namespace = repo_data.get('name_with_namespace', '')
                            existing_repo.description = repo_data.get('description', '')
                            existing_repo.web_url = repo_data.get('web_url', '')
                            existing_repo.ssh_url_to_repo = repo_data.get('ssh_url_to_repo', '')
                            existing_repo.http_url_to_repo = repo_data.get('http_url_to_repo', '')
                            existing_repo.default_branch = repo_data.get('default_branch', '')
                            existing_repo.visibility = repo_data.get('visibility', '')
                            existing_repo.created_at = self._parse_datetime(repo_data.get('created_at'))
                            existing_repo.last_activity_at = self._parse_datetime(repo_data.get('last_activity_at'))
                            existing_repo.sync_time = datetime.now()
                        else:
                            # 创建新仓库记录
                            new_repo = GitlabRepository(
                                id=repo_data['id'],
                                name=repo_data.get('name', ''),
                                name_with_namespace=repo_data.get('name_with_namespace', ''),
                                description=repo_data.get('description', ''),
                                web_url=repo_data.get('web_url', ''),
                                ssh_url_to_repo=repo_data.get('ssh_url_to_repo', ''),
                                http_url_to_repo=repo_data.get('http_url_to_repo', ''),
                                default_branch=repo_data.get('default_branch', ''),
                                visibility=repo_data.get('visibility', ''),
                                created_at=self._parse_datetime(repo_data.get('created_at')),
                                last_activity_at=self._parse_datetime(repo_data.get('last_activity_at')),
                                sync_time=datetime.now()
                            )
                            db.add(new_repo)
                        
                        synced_count += 1
                        
                    except Exception as e:
                        print(f"Error syncing repository {repo_data.get('id', 'unknown')}: {e}")
                        continue
                
                db.commit()
                return SyncResult.create_success(synced_count, len(repositories))  # 修正：添加 total_found 参数
                
        except Exception as e:
            print(f"Error in sync_repositories: {e}")
            return SyncResult.create_failure(str(e))
    
    def sync_group(self, group_data: Dict) -> SyncResult:
        """同步单个组织数据"""
        try:
            with get_db_session() as db:
                existing_group = db.query(GitlabGroup).filter(
                    GitlabGroup.id == group_data['id']
                ).first()
                
                if existing_group:
                    # 更新现有组织
                    existing_group.name = group_data.get('name', '')
                    existing_group.path = group_data.get('path', '')
                    existing_group.description = group_data.get('description', '')
                    existing_group.web_url = group_data.get('web_url', '')
                    existing_group.visibility = group_data.get('visibility', '')
                    existing_group.created_at = self._parse_datetime(group_data.get('created_at'))
                    existing_group.sync_time = datetime.now()
                else:
                    # 创建新组织记录
                    new_group = GitlabGroup(
                        id=group_data['id'],
                        name=group_data.get('name', ''),
                        path=group_data.get('path', ''),
                        description=group_data.get('description', ''),
                        web_url=group_data.get('web_url', ''),
                        visibility=group_data.get('visibility', ''),
                        created_at=self._parse_datetime(group_data.get('created_at')),
                        sync_time=datetime.now()
                    )
                    db.add(new_group)
                
                db.commit()
                return SyncResult.create_success(1, 1)  # 修正：添加 total_found 参数
                
        except Exception as e:
            print(f"Error syncing group {group_data.get('id', 'unknown')}: {e}")
            return SyncResult.create_failure(str(e))
    
    def sync_group_members(self, group_id: int, members: List[Dict]) -> SyncResult:
        """同步组织成员数据"""
        try:
            with get_db_session() as db:
                # 删除现有成员记录
                db.query(GitlabGroupMember).filter(
                    GitlabGroupMember.group_id == group_id
                ).delete()
                
                synced_count = 0
                for member_data in members:
                    try:
                        new_member = GitlabGroupMember(
                            group_id=group_id,
                            user_id=member_data['id'],
                            username=member_data.get('username', ''),
                            name=member_data.get('name', ''),
                            email=member_data.get('email', ''),
                            access_level=member_data.get('access_level', 0),
                            access_level_name=self._get_access_level_name(member_data.get('access_level', 0)),
                            sync_time=datetime.now()
                        )
                        db.add(new_member)
                        synced_count += 1
                        
                    except Exception as e:
                        print(f"Error syncing member {member_data.get('id', 'unknown')}: {e}")
                        continue
                
                db.commit()
                return SyncResult.create_success(synced_count, len(members))  # 修正：添加 total_found 参数
                
        except Exception as e:
            print(f"Error syncing group members for group {group_id}: {e}")
            return SyncResult.create_failure(str(e))
    
    def sync_repository_branches(self, repository_id: int, branches: List[Dict]) -> SyncResult:
        """同步仓库分支数据"""
        try:
            with get_db_session() as db:
                # 删除现有分支记录
                db.query(GitlabRepositoryBranch).filter(
                    GitlabRepositoryBranch.repository_id == repository_id
                ).delete()
                
                synced_count = 0
                for branch_data in branches:
                    try:
                        new_branch = GitlabRepositoryBranch(
                            repository_id=repository_id,
                            branch_name=branch_data.get('branch_name', ''),
                            commit_id=branch_data.get('commit_id', ''),
                            commit_message=branch_data.get('commit_message', ''),
                            commit_author_name=branch_data.get('commit_author_name', ''),
                            commit_author_email=branch_data.get('commit_author_email', ''),
                            last_commit_date=self._parse_datetime(branch_data.get('last_commit_date')),
                            protected=branch_data.get('protected', False),
                            sync_time=datetime.now()
                        )
                        db.add(new_branch)
                        synced_count += 1
                        
                    except Exception as e:
                        print(f"Error syncing branch {branch_data.get('branch_name', 'unknown')}: {e}")
                        continue
                
                db.commit()
                return SyncResult.create_success(synced_count, len(branches))  # 修正：添加 total_found 参数
                
        except Exception as e:
            print(f"Error syncing branches for repository {repository_id}: {e}")
            return SyncResult.create_failure(str(e))
    
    def sync_repository_permissions(self, repository_id: int, permissions: List[Dict]) -> SyncResult:
        """同步仓库权限数据"""
        try:
            with get_db_session() as db:
                # 删除现有权限记录
                db.query(GitlabRepositoryPermission).filter(
                    GitlabRepositoryPermission.repository_id == repository_id
                ).delete()
                
                synced_count = 0
                for perm_data in permissions:
                    try:
                        new_permission = GitlabRepositoryPermission(
                            repository_id=repository_id,
                            member_type=perm_data.get('member_type', ''),
                            member_id=perm_data.get('member_id', 0),
                            member_name=perm_data.get('member_name', ''),
                            access_level=perm_data.get('access_level', 0),
                            access_level_name=perm_data.get('access_level_name', ''),
                            sync_time=datetime.now()
                        )
                        db.add(new_permission)
                        synced_count += 1
                        
                    except Exception as e:
                        print(f"Error syncing permission for member {perm_data.get('member_id', 'unknown')}: {e}")
                        continue
                
                db.commit()
                return SyncResult.create_success(synced_count, len(permissions))  # 修正：添加 total_found 参数
                
        except Exception as e:
            print(f"Error syncing permissions for repository {repository_id}: {e}")
            return SyncResult.create_failure(str(e))
    
    def get_all_repository_ids(self) -> List[RepositoryId]:
        """获取所有仓库ID"""
        try:
            with get_db_session() as db:
                repositories = db.query(GitlabRepository.id).all()
                return RepositoryId.from_list(repositories)
        except Exception as e:
            print(f"Error getting repository IDs: {e}")
            return []
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """解析日期时间字符串"""
        if not datetime_str:
            return None
        try:
            # 处理 ISO 8601 格式
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception:
            return None
    
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
    
    # ==================== Tag 相关数据库操作 ====================
    
    def create_or_update_tag_relation(self, field_name: str, tag_name: str, 
                                      user: str, description: str) -> Dict[str, any]:
        """创建或更新 GitLab Tag 关联记录
        
        Args:
            field_name: 仓库对应的字段名 (如 'apk_tag', 'nena_tag')
            tag_name: Tag 名称
            user: 用户名
            description: 描述信息
            
        Returns:
            {'success': bool, 'action': 'created'|'updated', 'error': str}
        """
        from database.models import GitlabTagRelation
        
        try:
            with get_db_session() as db:
                # 查找是否已存在
                existing_relation = db.query(GitlabTagRelation).filter(
                    getattr(GitlabTagRelation, field_name) == tag_name
                ).first()
                
                if existing_relation:
                    # 更新现有记录
                    setattr(existing_relation, field_name, tag_name)
                    existing_relation.user = user
                    existing_relation.description = description
                    existing_relation.sync_time = datetime.now()
                    action = 'updated'
                else:
                    # 创建新记录
                    tag_relation = GitlabTagRelation(
                        **{field_name: tag_name},
                        user=user,
                        description=description,
                        created_at=datetime.now(),
                        sync_time=datetime.now()
                    )
                    db.add(tag_relation)
                    action = 'created'
                
                db.commit()
                return {'success': True, 'action': action}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== 子模块更新记录相关 ====================
    
    def create_submodule_update_record(self, parent_project_id: int, 
                                       target_branch: str, status: str,
                                       details: any = None) -> Dict[str, any]:
        """创建子模块更新记录
        
        Args:
            parent_project_id: 父项目ID
            target_branch: 目标分支名
            status: 状态 ('success' 或 'failure')
            details: 详细信息（JSON 格式）
            
        Returns:
            {'success': bool, 'error': str}
        """
        from database.models import GitlabSubmoduleUpdateRecord
        
        try:
            with get_db_session() as db:
                record = GitlabSubmoduleUpdateRecord(
                    parent_project_id=parent_project_id,
                    target_branch=target_branch,
                    status=status,
                    details=details,
                    created_at=datetime.now()
                )
                db.add(record)
                db.commit()
                return {'success': True}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_branch_creation_record(
        self,
        project_id: int,
        branch_name: str,
        source_ref: str,
        source_commit: str,
        status: str = 'created',
        message: Optional[str] = None,
        created_by: Optional[str] = None,
        jira_ticket: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建分支创建记录
        
        Args:
            project_id: 项目ID
            branch_name: 分支名称
            source_ref: 源引用（分支/tag）
            source_commit: 源提交SHA
            status: 状态（'created', 'failed'等）
            message: 消息
            created_by: 创建者
            jira_ticket: JIRA 工单号
            
        Returns:
            {'success': bool, 'record_id': int, 'error': str}
        """
        from database.models import GitlabBranchCreateRecord
        
        try:
            with get_db_session() as db:
                record = GitlabBranchCreateRecord(
                    project_id=project_id,
                    branch_name=branch_name,
                    source_ref=source_ref,
                    source_commit=source_commit,
                    status=status,
                    message=message,
                    created_at=datetime.now(),
                    created_by=created_by,
                    jira_ticket=jira_ticket
                )
                
                db.add(record)
                db.commit()
                db.refresh(record)
                
                return {
                    'success': True,
                    'record_id': record.id
                }
                
        except Exception as e:
            logger.exception('Failed to create branch creation record')
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_branch_summary(self, summary_data: dict) -> dict:
        """保存或更新分支汇总数据"""
        from database.models import GitlabBranchSummary
        
        try:
            with get_db_session() as db:
                # 检查是否已存在
                existing = db.query(GitlabBranchSummary).filter_by(
                    repository_id=summary_data['repository_id']
                ).first()
                
                if existing:
                    # 更新现有记录
                    for key, value in summary_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.data_version += 1
                    existing.last_sync_time = datetime.now()
                else:
                    # 创建新记录
                    summary = GitlabBranchSummary(**summary_data)
                    db.add(summary)
                
                db.commit()
                
                return {
                    'success': True,
                    'message': 'Branch summary saved successfully'
                }
                
        except Exception as e:
            logger.exception('Failed to save branch summary')
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_all_branch_summaries(self) -> dict:
        """删除所有分支汇总数据（用于强制刷新）"""
        from database.models import GitlabBranchSummary
        
        try:
            with get_db_session() as db:
                count = db.query(GitlabBranchSummary).delete()
                db.commit()
                
                return {
                    'success': True,
                    'count': count
                }
                
        except Exception as e:
            logger.exception('Failed to delete branch summaries')
            return {
                'success': False,
                'error': str(e)
            }