import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database.connection import get_db_session
from database.models import GitlabBranchRule, GitlabRepositoryBranch, GitlabRepository
from sqlalchemy import and_, or_
from dto.base_dto import BaseResult, CountableResult
from dto.branch_rule_dto import (
    BranchRuleData, BranchRuleTestResult, 
    BranchMatchResult
)
from dto.branch_deletion_dto import (
    BranchDeletionReport, DeletableBranchDetail
)
from dto.statistics_dto import BranchDeletionSummary, DeletionStatistics

# 使用基础结果类型
BranchRuleOperationResult = BaseResult
RuleApplicationResult = CountableResult

class BranchRuleService:
    def __init__(self):
        pass
    
    def create_rule(self, rule_data: Dict) -> BranchRuleOperationResult:
        """创建新的分支规则"""
        try:
            with get_db_session() as db:
                # 检查规则名称是否已存在
                existing = db.query(GitlabBranchRule).filter(
                    GitlabBranchRule.rule_name == rule_data['rule_name']
                ).first()
                
                if existing:
                    return BranchRuleOperationResult.create_failure(
                        f"Rule name '{rule_data['rule_name']}' already exists"
                    )
                
                # 创建新规则
                new_rule = GitlabBranchRule(
                    rule_name=rule_data['rule_name'],
                    branch_pattern=rule_data['branch_pattern'],
                    branch_type=rule_data['branch_type'],
                    is_deletable=rule_data.get('is_deletable', True),
                    retention_days=rule_data.get('retention_days'),
                    description=rule_data.get('description', ''),
                    is_active=rule_data.get('is_active', True),
                    priority=rule_data.get('priority', 0)
                )
                
                db.add(new_rule)
                db.commit()
                
                return BranchRuleOperationResult.create_success(
                    f"Rule '{rule_data['rule_name']}' created successfully"
                )
                
        except Exception as e:
            print(f"Error creating rule: {e}")
            return BranchRuleOperationResult.create_failure(str(e))
    
    def update_rule(self, rule_id: int, rule_data: Dict) -> BranchRuleOperationResult:
        """更新分支规则"""
        try:
            with get_db_session() as db:
                rule = db.query(GitlabBranchRule).filter(
                    GitlabBranchRule.id == rule_id
                ).first()
                
                if not rule:
                    return BranchRuleOperationResult.create_failure(
                        f"Rule with ID {rule_id} not found"
                    )
                
                # 检查规则名称是否与其他规则冲突
                if 'rule_name' in rule_data and rule_data['rule_name'] != rule.rule_name:
                    existing = db.query(GitlabBranchRule).filter(
                        GitlabBranchRule.rule_name == rule_data['rule_name'],
                        GitlabBranchRule.id != rule_id
                    ).first()
                    
                    if existing:
                        return BranchRuleOperationResult.create_failure(
                            f"Rule name '{rule_data['rule_name']}' already exists"
                        )
                
                # 更新字段
                updatable_fields = [
                    'rule_name', 'branch_pattern', 'branch_type', 
                    'is_deletable', 'retention_days', 'description', 
                    'is_active', 'priority'
                ]
                
                for field in updatable_fields:
                    if field in rule_data:
                        setattr(rule, field, rule_data[field])
                
                rule.updated_at = datetime.now()
                db.commit()
                
                return BranchRuleOperationResult.create_success(
                    f"Rule '{rule.rule_name}' updated successfully"
                )
                
        except Exception as e:
            print(f"Error updating rule {rule_id}: {e}")
            return BranchRuleOperationResult.create_failure(str(e))
    
    def delete_rule(self, rule_id: int) -> BranchRuleOperationResult:
        """删除分支规则"""
        try:
            with get_db_session() as db:
                rule = db.query(GitlabBranchRule).filter(
                    GitlabBranchRule.id == rule_id
                ).first()
                
                if not rule:
                    return BranchRuleOperationResult.create_failure(
                        f"Rule with ID {rule_id} not found"
                    )
                
                rule_name = rule.rule_name
                
                # 检查是否有分支正在使用这个规则
                branches_using_rule = db.query(GitlabRepositoryBranch).filter(
                    GitlabRepositoryBranch.matched_rule_id == rule_id
                ).count()
                
                if branches_using_rule > 0:
                    return BranchRuleOperationResult.create_failure(
                        f"Cannot delete rule '{rule_name}' as it is being used by {branches_using_rule} branches. Please apply rules again after deletion."
                    )
                
                db.delete(rule)
                db.commit()
                
                return BranchRuleOperationResult.create_success(
                    f"Rule '{rule_name}' deleted successfully"
                )
                
        except Exception as e:
            print(f"Error deleting rule {rule_id}: {e}")
            return BranchRuleOperationResult.create_failure(str(e))
    
    def get_rule_by_id(self, rule_id: int) -> Optional[BranchRuleData]:
        """根据ID获取单个规则"""
        try:
            with get_db_session() as db:
                rule = db.query(GitlabBranchRule).filter(
                    GitlabBranchRule.id == rule_id
                ).first()
                
                if not rule:
                    return None
                
                return BranchRuleData.from_model(rule)
                
        except Exception as e:
            print(f"Error getting rule {rule_id}: {e}")
            return None
    
    def get_all_rules(self, include_inactive: bool = True) -> List[BranchRuleData]:
        """获取所有规则"""
        try:
            with get_db_session() as db:
                query = db.query(GitlabBranchRule)
                
                if not include_inactive:
                    query = query.filter(GitlabBranchRule.is_active == True)
                
                rules = query.order_by(GitlabBranchRule.priority.desc()).all()
                
                result = []
                for rule in rules:
                    # 统计使用此规则的分支数量
                    branch_count = db.query(GitlabRepositoryBranch).filter(
                        GitlabRepositoryBranch.matched_rule_id == rule.id
                    ).count()
                    
                    result.append(BranchRuleData.from_model(rule, branch_count))
                
                return result
                
        except Exception as e:
            print(f"Error getting rules: {e}")
            return []
    
    def match_branch_rule(self, branch_name: str) -> Optional[GitlabBranchRule]:
        """根据分支名称匹配规则"""
        try:
            with get_db_session() as db:
                # 获取所有启用的规则，按优先级排序
                rules = db.query(GitlabBranchRule).filter(
                    GitlabBranchRule.is_active == True
                ).order_by(GitlabBranchRule.priority.desc()).all()
                
                for rule in rules:
                    if self._match_pattern(branch_name, rule.branch_pattern):
                        return rule
                
                return None
                
        except Exception as e:
            print(f"Error matching branch rule for {branch_name}: {e}")
            return None
    
    def _match_pattern(self, branch_name: str, pattern: str) -> bool:
        """匹配分支名称和模式"""
        # 支持通配符匹配
        if pattern == '*':
            return True
        
        # 支持多个模式用|分隔
        patterns = pattern.split('|')
        for p in patterns:
            p = p.strip()
            # 将通配符模式转换为正则表达式
            regex_pattern = p.replace('*', '.*').replace('?', '.')
            if re.match(f'^{regex_pattern}$', branch_name, re.IGNORECASE):
                return True
        
        return False
    
    def test_rule_pattern(self, pattern: str, test_branches: List[str]) -> BranchRuleTestResult:
        """测试规则模式是否匹配指定的分支名称"""
        try:
            results = []
            for branch_name in test_branches:
                is_match = self._match_pattern(branch_name, pattern)
                results.append({
                    'branch_name': branch_name,
                    'is_match': is_match
                })
            
            return BranchRuleTestResult.create_success(pattern, results)
            
        except Exception as e:
            return BranchRuleTestResult.create_failure(str(e))
    
    def apply_rules_to_branches(self, repository_id: int = None) -> RuleApplicationResult:
        """将规则应用到分支，标识哪些分支可删除"""
        try:
            with get_db_session() as db:
                # 获取需要处理的分支
                query = db.query(GitlabRepositoryBranch)
                if repository_id:
                    query = query.filter(GitlabRepositoryBranch.repository_id == repository_id)
                
                branches = query.all()
                
                updated_count = 0
                for branch in branches:
                    # 匹配规则
                    rule = self.match_branch_rule(branch.branch_name)
                    
                    if rule:
                        # 应用规则
                        branch.matched_rule_id = rule.id
                        branch.branch_type = rule.branch_type
                        
                        # 设置删除建议原因
                        deletion_reasons = []
                        
                        # 如果分支受保护，不建议删除
                        if branch.protected:
                            branch.is_deletable = False
                            deletion_reasons.append("分支受保护")
                        else:
                            # 根据规则判断是否可删除
                            branch.is_deletable = rule.is_deletable
                            
                            # 计算保留截止时间
                            if rule.retention_days and branch.last_commit_date:
                                branch.retention_deadline = branch.last_commit_date + timedelta(days=rule.retention_days)
                                
                                # 检查是否已过期
                                if datetime.now() > branch.retention_deadline:
                                    branch.is_deletable = True
                                    deletion_reasons.append(f"超过保留期限({rule.retention_days}天)")
                                else:
                                    days_left = (branch.retention_deadline - datetime.now()).days
                                    deletion_reasons.append(f"还有{days_left}天到期")
                            else:
                                branch.retention_deadline = None
                                if rule.is_deletable:
                                    deletion_reasons.append(f"根据规则'{rule.rule_name}'建议删除")
                        
                        # 添加额外的检查逻辑
                        if branch.branch_name in ['master', 'main', 'develop', 'dev']:
                            branch.is_deletable = False
                            deletion_reasons = ["核心分支，不建议删除"]
                        
                        branch.deletion_reason = "; ".join(deletion_reasons) if deletion_reasons else None
                        updated_count += 1
                
                db.commit()
                
                return RuleApplicationResult.create_success(
                    updated_count, 
                    f"Successfully applied rules to {updated_count}/{len(branches)} branches"
                )
                
        except Exception as e:
            print(f"Error applying rules to branches: {e}")
            return RuleApplicationResult.create_failure(str(e))
    
    def get_branch_deletion_report(self, repository_id: int = None) -> BranchDeletionReport:
        """获取分支删除建议报告"""
        try:
            with get_db_session() as db:
                query = db.query(GitlabRepositoryBranch).join(GitlabRepository)
                
                if repository_id:
                    query = query.filter(GitlabRepositoryBranch.repository_id == repository_id)
                
                all_branches = query.all()
                
                # 统计信息
                total_branches = len(all_branches)
                deletable_branches_list = [b for b in all_branches if b.is_deletable]
                protected_branches_list = [b for b in all_branches if b.protected]
                expired_branches_list = [b for b in deletable_branches_list if b.retention_deadline and datetime.now() > b.retention_deadline]
                
                summary = BranchDeletionSummary(
                    total=total_branches,
                    deletable=len(deletable_branches_list),
                    expired=len(expired_branches_list),
                    protected=len(protected_branches_list)
                )
                
                # 按分支类型分组
                branches_by_type = {}
                for branch in all_branches:
                    branch_type = branch.branch_type or 'unknown'
                    if branch_type not in branches_by_type:
                        branches_by_type[branch_type] = DeletionStatistics(
                            total=0,
                            deletable=0,
                            expired=0
                        )
                    
                    branches_by_type[branch_type].total += 1
                    if branch.is_deletable:
                        branches_by_type[branch_type].deletable += 1
                    if branch.retention_deadline and datetime.now() > branch.retention_deadline:
                        branches_by_type[branch_type].expired += 1
                
                # 详细的可删除分支列表
                deletable_list = [
                    DeletableBranchDetail.from_model(branch) 
                    for branch in deletable_branches_list
                ]
                
                return BranchDeletionReport(
                    summary=summary,
                    branches_by_type=branches_by_type,
                    deletable_branches=deletable_list
                )
                
        except Exception as e:
            print(f"Error getting branch deletion report: {e}")
            return BranchDeletionReport.create_empty()