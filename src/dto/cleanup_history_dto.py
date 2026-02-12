from datetime import datetime, date
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class CleanupHistoryData:
    """分支清理历史数据 DTO - 遵循项目命名规范"""
    report_date: date
    generation_time: datetime
    total_branches: int
    deletable_branches: int
    protected_branches: int
    expired_branches: int
    
    # 按类型统计
    feature_branches: int
    bugfix_branches: int
    hotfix_branches: int
    release_branches: int
    archive_branches: int
    main_branches: int
    other_branches: int
    
    # 按可删除类型统计
    deletable_feature: int
    deletable_bugfix: int
    deletable_archive: int
    deletable_other: int
    
    # 仓库维度统计
    total_repositories: int
    repositories_with_cleanup: int
    
    # 时间维度统计
    branches_over_30_days: int
    branches_over_60_days: int
    branches_over_90_days: int
    branches_over_180_days: int
    
    # 规则匹配统计
    matched_rules_count: int
    unmatched_branches: int
    
    # 可选字段
    estimated_storage_mb: float = None
    sync_version: str = None
    data_source: str = 'GitLab API'
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 - 遵循项目方法命名"""
        return {
            'report_date': self.report_date,
            'generation_time': self.generation_time,
            'total_branches': self.total_branches,
            'deletable_branches': self.deletable_branches,
            'protected_branches': self.protected_branches,
            'expired_branches': self.expired_branches,
            'feature_branches': self.feature_branches,
            'bugfix_branches': self.bugfix_branches,
            'hotfix_branches': self.hotfix_branches,
            'release_branches': self.release_branches,
            'archive_branches': self.archive_branches,
            'main_branches': self.main_branches,
            'other_branches': self.other_branches,
            'deletable_feature': self.deletable_feature,
            'deletable_bugfix': self.deletable_bugfix,
            'deletable_archive': self.deletable_archive,
            'deletable_other': self.deletable_other,
            'total_repositories': self.total_repositories,
            'repositories_with_cleanup': self.repositories_with_cleanup,
            'branches_over_30_days': self.branches_over_30_days,
            'branches_over_60_days': self.branches_over_60_days,
            'branches_over_90_days': self.branches_over_90_days,
            'branches_over_180_days': self.branches_over_180_days,
            'matched_rules_count': self.matched_rules_count,
            'unmatched_branches': self.unmatched_branches,
            'estimated_storage_mb': self.estimated_storage_mb,
            'sync_version': self.sync_version,
            'data_source': self.data_source,
        }
    
    @classmethod
    def from_model(cls, model: 'GitlabBranchCleanupHistory') -> 'CleanupHistoryData':
        """从数据库模型创建 DTO - 遵循项目方法命名"""
        return cls(
            report_date=model.report_date,
            generation_time=model.generation_time,
            total_branches=model.total_branches,
            deletable_branches=model.deletable_branches,
            protected_branches=model.protected_branches,
            expired_branches=model.expired_branches,
            feature_branches=model.feature_branches,
            bugfix_branches=model.bugfix_branches,
            hotfix_branches=model.hotfix_branches,
            release_branches=model.release_branches,
            archive_branches=model.archive_branches,
            main_branches=model.main_branches,
            other_branches=model.other_branches,
            deletable_feature=model.deletable_feature,
            deletable_bugfix=model.deletable_bugfix,
            deletable_archive=model.deletable_archive,
            deletable_other=model.deletable_other,
            total_repositories=model.total_repositories,
            repositories_with_cleanup=model.repositories_with_cleanup,
            branches_over_30_days=model.branches_over_30_days,
            branches_over_60_days=model.branches_over_60_days,
            branches_over_90_days=model.branches_over_90_days,
            branches_over_180_days=model.branches_over_180_days,
            matched_rules_count=model.matched_rules_count,
            unmatched_branches=model.unmatched_branches,
            estimated_storage_mb=model.estimated_storage_mb,
            sync_version=model.sync_version,
            data_source=model.data_source,
        )
    
    def get_cleanup_rate(self) -> float:
        """计算清理率"""
        if self.total_branches == 0:
            return 0.0
        return round(self.deletable_branches / self.total_branches * 100, 2)