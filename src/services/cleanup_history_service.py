from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from sqlalchemy import func, case
from database.connection import get_db_session
from database.models import (
    GitlabRepositoryBranch, GitlabRepository, GitlabBranchRule,
    GitlabBranchCleanupHistory
)
from dto.cleanup_history_dto import CleanupHistoryData

class CleanupHistoryService:
    def __init__(self):
        pass
    
    def generate_daily_cleanup_summary(self, target_date: date = None) -> Dict[str, Any]:
        """生成每日分支清理汇总数据 - 使用 DTO 模式"""
        if target_date is None:
            target_date = date.today()
        
        try:
            with get_db_session() as db:
                # 检查是否已存在当日数据
                existing = db.query(GitlabBranchCleanupHistory).filter(
                    GitlabBranchCleanupHistory.report_date == target_date
                ).first()
                
                if existing:
                    # 删除已存在的数据，重新生成
                    db.delete(existing)
                    db.commit()
                
                # 收集统计数据并创建 DTO
                cleanup_data = self._collect_branch_statistics_as_dto(db, target_date)
                
                # 使用 DTO 创建数据库模型
                cleanup_summary = GitlabBranchCleanupHistory(**cleanup_data.to_dict())
                
                db.add(cleanup_summary)
                db.commit()
                
                print(f"Generated cleanup summary for {target_date}")
                print(f"Total branches: {cleanup_data.total_branches}, Deletable: {cleanup_data.deletable_branches}")
                print(f"Cleanup rate: {cleanup_data.get_cleanup_rate()}%")
                
                return {
                    'success': True,
                    'date': target_date,
                    'summary': cleanup_data.to_dict()
                }
                
        except Exception as e:
            print(f"Error generating cleanup summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _collect_branch_statistics_as_dto(self, db, target_date: date) -> CleanupHistoryData:
        """收集分支统计数据并返回 DTO"""
        
        # 基础查询
        all_branches = db.query(GitlabRepositoryBranch).join(GitlabRepository).all()
        
        # 基础统计
        total_branches = len(all_branches)
        deletable_branches = len([b for b in all_branches if b.is_deletable])
        protected_branches = len([b for b in all_branches if b.protected])
        
        # 计算过期分支（基于retention_deadline）
        now = datetime.now()
        expired_branches = len([
            b for b in all_branches 
            if b.retention_deadline and b.retention_deadline < now
        ])
        
        # 按分支类型统计
        type_stats = self._count_by_branch_type(all_branches)
        
        # 按可删除类型统计
        deletable_stats = self._count_deletable_by_type(all_branches)
        
        # 仓库维度统计
        repo_stats = self._count_repository_statistics(all_branches)
        
        # 时间维度统计
        time_stats = self._count_by_time_ranges(all_branches, now)
        
        # 规则匹配统计
        rule_stats = self._count_rule_matching(all_branches)
        
        # 创建并返回 DTO
        return CleanupHistoryData(
            report_date=target_date,
            generation_time=datetime.now(),
            total_branches=total_branches,
            deletable_branches=deletable_branches,
            protected_branches=protected_branches,
            expired_branches=expired_branches,
            **type_stats,
            **deletable_stats,
            **repo_stats,
            **time_stats,
            **rule_stats
        )
    
    def _count_by_branch_type(self, branches) -> Dict[str, int]:
        """按分支类型统计"""
        type_counts = {
            'feature_branches': 0,
            'bugfix_branches': 0,
            'hotfix_branches': 0,
            'release_branches': 0,
            'archive_branches': 0,
            'main_branches': 0,
            'other_branches': 0
        }
        
        for branch in branches:
            branch_type = branch.branch_type or 'other'
            if branch_type == 'feature':
                type_counts['feature_branches'] += 1
            elif branch_type in ['bugfix', 'bug']:
                type_counts['bugfix_branches'] += 1
            elif branch_type == 'hotfix':
                type_counts['hotfix_branches'] += 1
            elif branch_type == 'release':
                type_counts['release_branches'] += 1
            elif branch_type == 'archive':
                type_counts['archive_branches'] += 1
            elif branch_type in ['main', 'master']:
                type_counts['main_branches'] += 1
            else:
                type_counts['other_branches'] += 1
        
        return type_counts
    
    def _count_deletable_by_type(self, branches) -> Dict[str, int]:
        """按可删除类型统计"""
        deletable_counts = {
            'deletable_feature': 0,
            'deletable_bugfix': 0,
            'deletable_archive': 0,
            'deletable_other': 0
        }
        
        for branch in branches:
            if branch.is_deletable:
                branch_type = branch.branch_type or 'other'
                if branch_type == 'feature':
                    deletable_counts['deletable_feature'] += 1
                elif branch_type in ['bugfix', 'bug']:
                    deletable_counts['deletable_bugfix'] += 1
                elif branch_type == 'archive':
                    deletable_counts['deletable_archive'] += 1
                else:
                    deletable_counts['deletable_other'] += 1
        
        return deletable_counts
    
    def _count_repository_statistics(self, branches) -> Dict[str, int]:
        """仓库维度统计"""
        repo_ids = set(branch.repository_id for branch in branches)
        repos_with_cleanup = set(
            branch.repository_id for branch in branches if branch.is_deletable
        )
        
        return {
            'total_repositories': len(repo_ids),
            'repositories_with_cleanup': len(repos_with_cleanup)
        }
    
    def _count_by_time_ranges(self, branches, now: datetime) -> Dict[str, int]:
        """时间维度统计"""
        time_counts = {
            'branches_over_30_days': 0,
            'branches_over_60_days': 0,
            'branches_over_90_days': 0,
            'branches_over_180_days': 0
        }
        
        for branch in branches:
            if branch.last_commit_date:
                days_diff = (now - branch.last_commit_date).days
                if days_diff > 30:
                    time_counts['branches_over_30_days'] += 1
                if days_diff > 60:
                    time_counts['branches_over_60_days'] += 1
                if days_diff > 90:
                    time_counts['branches_over_90_days'] += 1
                if days_diff > 180:
                    time_counts['branches_over_180_days'] += 1
        
        return time_counts
    
    def _count_rule_matching(self, branches) -> Dict[str, int]:
        """规则匹配统计"""
        matched_count = len([b for b in branches if b.matched_rule_id])
        unmatched_count = len([b for b in branches if not b.matched_rule_id])
        
        return {
            'matched_rules_count': matched_count,
            'unmatched_branches': unmatched_count
        }
    
    def get_cleanup_trend(self, days: int = 30) -> List[CleanupHistoryData]:
        """获取清理趋势数据 - 返回 DTO 列表"""
        try:
            with get_db_session() as db:
                end_date = date.today()
                start_date = end_date - timedelta(days=days)
                
                histories = db.query(GitlabBranchCleanupHistory).filter(
                    GitlabBranchCleanupHistory.report_date >= start_date,
                    GitlabBranchCleanupHistory.report_date <= end_date
                ).order_by(GitlabBranchCleanupHistory.report_date).all()
                
                # 转换为 DTO 列表
                trend_data = [CleanupHistoryData.from_model(history) for history in histories]
                
                return trend_data
                
        except Exception as e:
            print(f"Error getting cleanup trend: {e}")
            return []