from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from .base_dto import DataTransformMixin

@dataclass
class BranchExportData(DataTransformMixin):
    """分支导出数据 DTO"""
    repository_id: int
    repository_name: str
    name_with_namespace: str  # 添加这个字段
    branch_name: str
    branch_type: Optional[str]
    last_commit_date: Optional[datetime]
    commit_author_name: Optional[str]
    commit_author_email: Optional[str]
    commit_message: Optional[str]
    protected: bool
    
    # 数据库中存储的值
    db_deletable: bool
    db_deadline: Optional[datetime]
    db_reason: Optional[str]
    
    # 计算得出的值
    computed_type: Optional[str]
    computed_deletable: bool
    computed_deadline: Optional[datetime]
    computed_reason: Optional[str]
    matched_rule_name: Optional[str]
    
    @classmethod
    def from_model(cls, branch, rule_result: Dict[str, Any] = None) -> 'BranchExportData':
        """从分支模型和规则结果创建 DTO"""
        if rule_result is None:
            rule_result = {}
        
        return cls(
            repository_id=branch.repository_id,
            repository_name=branch.repository.name if branch.repository else 'Unknown',
            name_with_namespace=branch.repository.name_with_namespace if branch.repository else '',  # 添加这行
            branch_name=branch.branch_name,
            branch_type=branch.branch_type,
            last_commit_date=branch.last_commit_date,
            commit_author_name=branch.commit_author_name,
            commit_author_email=branch.commit_author_email,
            commit_message=branch.commit_message,
            protected=branch.protected,
            
            # 数据库中的值
            db_deletable=branch.is_deletable or False,
            db_deadline=branch.retention_deadline,
            db_reason=branch.deletion_reason,
            
            # 计算的值
            computed_type=rule_result.get('branch_type', branch.branch_type),
            computed_deletable=rule_result.get('is_deletable', branch.is_deletable or False),
            computed_deadline=rule_result.get('retention_deadline', branch.retention_deadline),
            computed_reason=rule_result.get('deletion_reason', branch.deletion_reason),
            matched_rule_name=rule_result.get('matched_rule_name')
        )
    
    def is_expired(self) -> bool:
        """检查分支是否已过期"""
        if not self.computed_deadline:
            return False
        return datetime.now() > self.computed_deadline
    
    def get_status_description(self) -> str:
        """获取分支状态描述"""
        if self.protected:
            return "受保护"
        elif self.computed_deletable:
            if self.is_expired():
                return "已过期，建议删除"
            else:
                return "可删除"
        else:
            return "保留"
    
    def get_days_until_deadline(self) -> Optional[int]:
        """获取距离截止时间的天数"""
        if not self.computed_deadline:
            return None
        
        delta = self.computed_deadline - datetime.now()
        return delta.days if delta.days >= 0 else 0