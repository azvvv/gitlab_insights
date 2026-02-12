from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .base_dto import BaseResult, CountableResult, DataTransformMixin

@dataclass
class BranchRuleData(DataTransformMixin):
    """分支规则数据 DTO"""
    id: int
    rule_name: str
    branch_pattern: str
    branch_type: str
    is_deletable: bool
    retention_days: Optional[int]
    description: Optional[str]
    is_active: bool
    priority: int
    created_at: str
    updated_at: str
    branch_count: Optional[int] = None
    
    @classmethod
    def from_model(cls, rule, branch_count: int = None) -> 'BranchRuleData':
        """从数据库模型创建 DTO"""
        return cls(
            id=rule.id,
            rule_name=rule.rule_name,
            branch_pattern=rule.branch_pattern,
            branch_type=rule.branch_type,
            is_deletable=rule.is_deletable,
            retention_days=rule.retention_days,
            description=rule.description,
            is_active=rule.is_active,
            priority=rule.priority,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat(),
            branch_count=branch_count
        )

# 使用基础结果类
BranchRuleOperationResult = BaseResult

@dataclass
class BranchRuleTestResult(BaseResult):
    """分支规则测试结果 DTO"""
    pattern: str = ""
    results: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
    
    @classmethod
    def create_success(cls, pattern: str, results: List[Dict[str, Any]]) -> 'BranchRuleTestResult':
        """创建成功的测试结果"""
        return cls(success=True, pattern=pattern, results=results, message="Test completed")
    
    @classmethod
    def create_failure(cls, error: str) -> 'BranchRuleTestResult':
        """创建失败的测试结果"""
        return cls(success=False, pattern="", results=[], error=error)

@dataclass
class BranchMatchResult:
    """分支匹配结果 DTO"""
    branch_name: str
    is_match: bool

# 使用基础计数结果类
RuleApplicationResult = CountableResult