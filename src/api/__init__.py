"""
API Blueprint 注册中心
统一管理所有业务模块的 Blueprint
"""
from flask import Flask


def register_blueprints(app: Flask):
    """
    注册所有 API Blueprint
    
    Args:
        app: Flask 应用实例
    """
    # 1. 认证模块
    from api.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # 2. 首页链接配置
    from api.home_link_routes import home_link_bp
    app.register_blueprint(home_link_bp, url_prefix='/api/home-links')
    
    # 3. GitLab 数据同步和查询
    from api.gitlab_routes import gitlab_bp
    app.register_blueprint(gitlab_bp, url_prefix='/api/gitlab')
    
    # 4. 监控服务（指标、调度器）
    from api.monitoring_routes import monitoring_bp
    app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')
    
    # 6. 任务管理
    from api.task_routes import task_bp
    app.register_blueprint(task_bp, url_prefix='/api/tasks')
    
    # 7. 分支规则管理
    from api.branch_rule_routes import branch_rule_bp
    app.register_blueprint(branch_rule_bp, url_prefix='/api/branch-rules')
    
    # 8. 日志管理
    from api.log_routes import log_bp
    app.register_blueprint(log_bp, url_prefix='/api')
    
    # 10. 系统级路由（health, statistics, init-db）
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    print("✅ API Blueprints 注册成功: auth, home-links, gitlab, monitoring, tasks, branch-rules, logs, system")