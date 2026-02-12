from dataclasses import dataclass
from typing import Dict, List
from .base_dto import StatisticsBase

@dataclass
class DeletionStatistics(StatisticsBase):
    """删除统计基础 DTO"""
    deletable: int = 0
    expired: int = 0
    
    def get_deletable_percentage(self) -> float:
        """获取可删除百分比"""
        return self.get_percentage(self.deletable)
    
    def get_expired_percentage(self) -> float:
        """获取已过期百分比"""
        return self.get_percentage(self.expired)

@dataclass
class BranchDeletionSummary(DeletionStatistics):
    """分支删除摘要 DTO"""
    protected: int = 0
    
    def get_protected_percentage(self) -> float:
        """获取受保护分支百分比"""
        return self.get_percentage(self.protected)

# BranchTypeStatistics 现在可以直接使用 DeletionStatistics
BranchTypeStatistics = DeletionStatistics