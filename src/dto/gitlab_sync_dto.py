from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class RepositorySyncResult:
    """仓库同步结果 DTO"""
    success: bool
    synced_count: int
    total_found: int
    message: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def create_success(cls, synced_count: int, total_found: int) -> 'RepositorySyncResult':
        """创建成功结果"""
        return cls(
            success=True,
            synced_count=synced_count,
            total_found=total_found,
            message=f'Successfully synced {synced_count} repositories'
        )
    
    @classmethod
    def create_failure(cls, error: str) -> 'RepositorySyncResult':
        """创建失败结果"""
        return cls(
            success=False,
            synced_count=0,
            total_found=0,
            error=error
        )

@dataclass
class GroupSyncResult:
    """组织同步结果 DTO"""
    success: bool
    synced_groups: int
    synced_members: int
    total_groups_found: int
    message: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def create_success(cls, synced_groups: int, synced_members: int, total_groups_found: int) -> 'GroupSyncResult':
        """创建成功结果"""
        return cls(
            success=True,
            synced_groups=synced_groups,
            synced_members=synced_members,
            total_groups_found=total_groups_found,
            message=f'Successfully synced {synced_groups} groups and {synced_members} members'
        )
    
    @classmethod
    def create_failure(cls, error: str) -> 'GroupSyncResult':
        """创建失败结果"""
        return cls(
            success=False,
            synced_groups=0,
            synced_members=0,
            total_groups_found=0,
            error=error
        )

@dataclass
class BranchSyncResult:
    """分支同步结果 DTO"""
    success: bool
    synced_branches: int
    processed_repositories: int
    total_repositories: int
    message: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def create_success(cls, synced_branches: int, processed_repositories: int, total_repositories: int) -> 'BranchSyncResult':
        """创建成功结果"""
        return cls(
            success=True,
            synced_branches=synced_branches,
            processed_repositories=processed_repositories,
            total_repositories=total_repositories,
            message=f'Successfully synced {synced_branches} branches for {processed_repositories} repositories'
        )
    
    @classmethod
    def create_failure(cls, error: str, processed_repositories: int = 0) -> 'BranchSyncResult':
        """创建失败结果"""
        return cls(
            success=False,
            synced_branches=0,
            processed_repositories=processed_repositories,
            total_repositories=0,
            error=error
        )

@dataclass
class PermissionSyncResult:
    """权限同步结果 DTO"""
    success: bool
    synced_permissions: int
    processed_repositories: int
    total_repositories: int
    message: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def create_success(cls, synced_permissions: int, processed_repositories: int, total_repositories: int) -> 'PermissionSyncResult':
        """创建成功结果"""
        return cls(
            success=True,
            synced_permissions=synced_permissions,
            processed_repositories=processed_repositories,
            total_repositories=total_repositories,
            message=f'Successfully synced {synced_permissions} permissions for {processed_repositories} repositories'
        )
    
    @classmethod
    def create_failure(cls, error: str, processed_repositories: int = 0) -> 'PermissionSyncResult':
        """创建失败结果"""
        return cls(
            success=False,
            synced_permissions=0,
            processed_repositories=processed_repositories,
            total_repositories=0,
            error=error
        )

@dataclass
class AllSyncResult:
    """全量同步结果 DTO"""
    success: bool
    repositories: RepositorySyncResult
    groups: GroupSyncResult
    branches: BranchSyncResult
    permissions: PermissionSyncResult
    message: str
    
    @classmethod
    def create_from_results(
        cls, 
        repositories: RepositorySyncResult,
        groups: GroupSyncResult,
        branches: BranchSyncResult,
        permissions: PermissionSyncResult
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