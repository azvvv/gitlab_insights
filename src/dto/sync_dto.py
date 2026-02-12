from typing import List, Dict, Optional
from dataclasses import dataclass
from .base_dto import SyncResult, CountableResult

@dataclass
class RepositoryId:
    """仓库ID DTO"""
    id: int
    
    @classmethod
    def from_list(cls, repo_list) -> List['RepositoryId']:
        """从查询结果列表创建 DTO 列表"""
        return [cls(id=repo.id) for repo in repo_list]

# 特定的同步结果，继承基础类
@dataclass
class GroupSyncResult(SyncResult):
    """组织同步结果 DTO"""
    synced_members: int = 0
    
    @classmethod
    def create_success(cls, synced_groups: int, synced_members: int, total_found: int) -> 'GroupSyncResult':
        """创建成功结果"""
        message = f'Successfully synced {synced_groups} groups and {synced_members} members'
        return cls(
            success=True,
            count=synced_groups,
            total_found=total_found,
            synced_members=synced_members,
            message=message
        )

@dataclass
class BranchSyncResult(SyncResult):
    """分支同步结果 DTO"""
    processed_repositories: int = 0
    total_repositories: int = 0
    
    @classmethod
    def create_success(cls, synced_branches: int, processed_repositories: int, total_repositories: int) -> 'BranchSyncResult':
        """创建成功结果"""
        message = f'Successfully synced {synced_branches} branches for {processed_repositories} repositories'
        return cls(
            success=True,
            count=synced_branches,
            processed_repositories=processed_repositories,
            total_repositories=total_repositories,
            message=message
        )

@dataclass
class AllSyncResult:
    """全量同步结果汇总 DTO"""
    success: bool
    repositories: SyncResult
    groups: GroupSyncResult
    branches: BranchSyncResult
    permissions: SyncResult
    message: str
    
    @classmethod
    def create_from_results(
        cls, 
        repositories: SyncResult,
        groups: GroupSyncResult,
        branches: BranchSyncResult,
        permissions: SyncResult
    ) -> 'AllSyncResult':
        """从各个同步结果创建全量同步结果"""
        total_success = all([
            repositories.success,
            groups.success,
            branches.success,
            permissions.success
        ])
        
        message = 'All sync completed' if total_success else 'Some sync operations failed'
        
        return cls(
            success=total_success,
            repositories=repositories,
            groups=groups,
            branches=branches,
            permissions=permissions,
            message=message
        )