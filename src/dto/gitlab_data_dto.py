from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from .base_dto import DataTransformMixin

@dataclass
class GitlabRepositoryData(DataTransformMixin):
    """GitLab 仓库数据 DTO"""
    id: int
    name: str
    name_with_namespace: str
    description: Optional[str]
    web_url: str
    ssh_url_to_repo: str
    http_url_to_repo: str
    default_branch: Optional[str]
    visibility: str
    created_at: Optional[str]
    last_activity_at: Optional[str]
    
    @classmethod
    def from_model(cls, project) -> 'GitlabRepositoryData':
        """从 GitLab 项目对象创建 DTO"""
        return cls(
            id=project.id,
            name=project.name,
            name_with_namespace=project.name_with_namespace,
            description=project.description,
            web_url=project.web_url,
            ssh_url_to_repo=project.ssh_url_to_repo,
            http_url_to_repo=project.http_url_to_repo,
            default_branch=project.default_branch,
            visibility=project.visibility,
            created_at=project.created_at,
            last_activity_at=project.last_activity_at
        )

@dataclass
class GitlabGroupData(DataTransformMixin):
    """GitLab 组织数据 DTO"""
    id: int
    name: str
    path: str
    description: Optional[str]
    web_url: str
    visibility: str
    created_at: Optional[str]
    
    @classmethod
    def from_model(cls, group) -> 'GitlabGroupData':
        """从 GitLab 组织对象创建 DTO"""
        return cls(
            id=group.id,
            name=group.name,
            path=group.path,
            description=group.description,
            web_url=group.web_url,
            visibility=group.visibility,
            created_at=group.created_at
        )

@dataclass
class GitlabMemberData(DataTransformMixin):
    """GitLab 成员数据 DTO"""
    id: int
    username: str
    name: str
    email: str
    access_level: int
    
    @classmethod
    def from_model(cls, member) -> 'GitlabMemberData':
        """从 GitLab 成员对象创建 DTO"""
        return cls(
            id=member.id,
            username=member.username,
            name=member.name,
            email=getattr(member, 'email', ''),
            access_level=member.access_level
        )

@dataclass
class GitlabBranchData(DataTransformMixin):
    """GitLab 分支数据 DTO"""
    branch_name: str
    commit_id: str
    commit_message: Optional[str]
    commit_author_name: Optional[str]
    commit_author_email: Optional[str]
    last_commit_date: Optional[str]
    protected: bool
    
    @classmethod
    def from_model(cls, branch, commit=None) -> 'GitlabBranchData':
        """从 GitLab 分支对象创建 DTO"""
        if commit:
            return cls(
                branch_name=branch.name,
                commit_id=branch.commit['id'],
                commit_message=commit.message,
                commit_author_name=commit.author_name,
                commit_author_email=commit.author_email,
                last_commit_date=commit.committed_date,
                protected=branch.protected
            )
        else:
            return cls(
                branch_name=branch.name,
                commit_id=branch.commit['id'],
                commit_message=branch.commit.get('message', ''),
                commit_author_name=branch.commit.get('author_name', ''),
                commit_author_email=branch.commit.get('author_email', ''),
                last_commit_date=branch.commit.get('committed_date'),
                protected=branch.protected
            )

@dataclass
class GitlabPermissionData(DataTransformMixin):
    """GitLab 权限数据 DTO"""
    member_type: str
    member_id: int
    member_name: str
    access_level: int
    access_level_name: str
    
    @classmethod
    def from_model(cls, member, access_level_name: str) -> 'GitlabPermissionData':
        """从 GitLab 成员对象创建权限 DTO"""
        member_type = 'group' if hasattr(member, 'group_access') else 'user'
        
        return cls(
            member_type=member_type,
            member_id=member.id,
            member_name=getattr(member, 'name', getattr(member, 'username', '')),
            access_level=member.access_level,
            access_level_name=access_level_name
        )