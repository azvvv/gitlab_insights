from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class BranchDeletionSummary:
    """分支删除摘要 DTO"""
    total_branches: int
    deletable_branches: int
    protected_branches: int
    expired_branches: int
    
    def get_deletable_percentage(self) -> float:
        """获取可删除分支百分比"""
        if self.total_branches == 0:
            return 0.0
        return (self.deletable_branches / self.total_branches) * 100
    
    def get_expired_percentage(self) -> float:
        """获取已过期分支百分比"""
        if self.total_branches == 0:
            return 0.0
        return (self.expired_branches / self.total_branches) * 100

@dataclass
class BranchTypeStatistics:
    """分支类型统计 DTO"""
    total: int
    deletable: int
    expired: int
    
    def get_deletable_percentage(self) -> float:
        """获取可删除百分比"""
        if self.total == 0:
            return 0.0
        return (self.deletable / self.total) * 100

@dataclass
class DeletableBranchDetail:
    """可删除分支详情 DTO"""
    id: int
    repository_id: int
    repository_name: str
    branch_name: str
    branch_type: Optional[str]
    last_commit_date: Optional[str]
    retention_deadline: Optional[str]
    is_expired: bool
    deletion_reason: Optional[str]
    matched_rule_id: Optional[int]
    protected: bool
    
    @classmethod
    def from_branch_model(cls, branch) -> 'DeletableBranchDetail':
        """从分支模型创建 DTO"""
        return cls(
            id=branch.id,
            repository_id=branch.repository_id,
            repository_name=branch.repository.name if branch.repository else 'Unknown',
            branch_name=branch.branch_name,
            branch_type=branch.branch_type,
            last_commit_date=branch.last_commit_date.isoformat() if branch.last_commit_date else None,
            retention_deadline=branch.retention_deadline.isoformat() if branch.retention_deadline else None,
            is_expired=branch.retention_deadline and datetime.now() > branch.retention_deadline if branch.retention_deadline else False,
            deletion_reason=branch.deletion_reason,
            matched_rule_id=branch.matched_rule_id,
            protected=branch.protected
        )

@dataclass
class BranchDeletionReport:
    """分支删除报告 DTO"""
    summary: BranchDeletionSummary
    branches_by_type: Dict[str, BranchTypeStatistics]
    deletable_branches: List[DeletableBranchDetail]
    
    @classmethod
    def create_empty(cls) -> 'BranchDeletionReport':
        """创建空报告"""
        return cls(
            summary=BranchDeletionSummary(0, 0, 0, 0),
            branches_by_type={},
            deletable_branches=[]
        )