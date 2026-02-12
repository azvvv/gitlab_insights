"""
系统级路由

仅保留核心系统功能路由：
- 健康检查
- 系统统计
- 数据库初始化

其他业务路由已迁移到各自的 Blueprint 模块
"""

from flask import Blueprint
from sqlalchemy import func

from database.connection import get_db_session, initialize_database
from database.models import GitlabRepository, GitlabGroup, GitlabRepositoryBranch, LogImportStatus
from api.response import api_response
from utils.errorhandler import handle_exceptions

api_bp = Blueprint('api', __name__)

# ==================== 认证相关 API ====================
# 已迁移到 api/auth_routes.py (8个路由)
# - POST /api/auth/login
# - POST /api/auth/ldap-login  
# - POST /api/auth/auto-login
# - GET  /api/auth/verify
# - GET  /api/auth/me
# - POST /api/auth/change-password
# - GET  /api/auth/ldap/test
# - GET  /api/auth/ldap/config

# ==================== 原有 API ====================

# ==================== 日志管理 API ====================
# 已迁移到 api/log_routes.py (4个路由)
# - POST /api/parse-log
# - GET  /api/status
# - GET  /api/import-history
# - GET  /api/logs

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return api_response(status='healthy')

@api_bp.route('/statistics', methods=['GET'])
@handle_exceptions
def get_statistics():
    """获取系统统计数据"""
    with get_db_session() as db:
        # 统计仓库数量
        repo_count = db.query(GitlabRepository).count()
        
        # 统计分组数量
        group_count = db.query(GitlabGroup).count()
        
        # 统计分支数量
        branch_count = db.query(GitlabRepositoryBranch).count()
        
        # 统计日志记录数量
        log_count = db.query(func.sum(LogImportStatus.record_count)).scalar() or 0
        
        return api_response(
            repositories=repo_count,
            groups=group_count,
            branches=branch_count,
            logs=log_count
        )

@api_bp.route('/init-db', methods=['POST'])
@handle_exceptions
def init_database():
    """初始化数据库表"""
    initialize_database()
    return api_response(message='Database initialized successfully')

# ==================== GitLab 数据同步和查询 API ====================
# 已迁移到 api/gitlab_routes.py (11个路由)
# 数据同步:
# - POST /api/gitlab/sync-repositories
# - POST /api/gitlab/sync-groups
# - POST /api/gitlab/sync-branches
# - POST /api/gitlab/sync-permissions
# - POST /api/gitlab/sync-all
# 数据查询:
# - GET  /api/gitlab/repositories
# - GET  /api/gitlab/groups
# - GET  /api/gitlab/repository/<repo_id>/branches
# - GET  /api/gitlab/repository/<repo_id>/permissions
# Tag 创建:
# - POST /api/gitlab/create-tag

# ==================== 任务管理 API ====================
# 已迁移到 api/task_routes.py (3个路由)
# - GET  /api/tasks/<task_id>
# - GET  /api/tasks
# - POST /api/tasks/<task_id>/cancel

# ==================== 分支规则管理 API ====================
# 已迁移到 api/branch_rule_routes.py (8个路由)
# - GET    /api/branch-rules
# - POST   /api/branch-rules
# - GET    /api/branch-rules/<rule_id>
# - PUT    /api/branch-rules/<rule_id>
# - DELETE /api/branch-rules/<rule_id>
# - POST   /api/branch-rules/test-pattern
# - POST   /api/branch-rules/apply
# - GET    /api/branch-rules/deletion-report/excel
# - GET    /api/branch-rules/deletion-report

# ==================== 监控服务 API ====================
# 已迁移到 api/monitoring_routes.py
# 指标:
# - GET /api/monitoring/metrics
# - GET /api/monitoring/metrics/latest
# - GET /api/monitoring/metrics/trend
# - GET /api/monitoring/applications/<application>/summary
# 调度器:
# - GET  /api/monitoring/scheduler/status
# - POST /api/monitoring/scheduler/jobs/<job_id>/run

# ==================== 首页链接配置 API ====================
# 已迁移到 api/home_link_routes.py (9个路由)
# - GET    /api/home-links
# - GET    /api/home-links/category/<category>
# - GET    /api/home-links/category/<category>/group/<group_name>
# - GET    /api/home-links/<link_id>
# - POST   /api/home-links
# - PUT    /api/home-links/<link_id>
# - DELETE /api/home-links/<link_id>
# - POST   /api/home-links/<link_id>/toggle
# - PUT    /api/home-links/sort

def setup_routes(app):
    """
    注册路由到Flask应用
    
    注意：此函数已废弃，请使用 api/__init__.py 中的 register_blueprints()
    保留此函数仅为向后兼容
    """
    from api import register_blueprints
    register_blueprints(app)