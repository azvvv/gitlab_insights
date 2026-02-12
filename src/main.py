'''
Author: yang_x_neu azvvv2023@outlook.com
Date: 2025-06-13 16:12:56
LastEditors: yang_x_neu azvvv2023@outlook.com
LastEditTime: 2025-06-20 08:59:36
FilePath: \gitlab_insight\src\main.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''

from dotenv import load_dotenv
import json

# 加载环境变量（settings 会自动加载，这里保留以确保兼容性）
load_dotenv()

from flask import Flask
from flask.json.provider import DefaultJSONProvider
from database.connection import initialize_database
from api import register_blueprints
from config.logging_config import init_logging
from middleware.logging_middleware import LoggingMiddleware
from utils.logger import get_logger
from config.settings import settings
from services.scheduler import monitoring_scheduler

# 初始化日志系统（在应用创建之前）
init_logging()
logger = get_logger(__name__)


class InternationalJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        # 不转义非 ASCII 字符，支持全球所有语言
        kwargs.setdefault('ensure_ascii', False)
        # 开发环境格式化输出，生产环境紧凑输出
        if kwargs.get('indent') is None:
            from flask import current_app
            kwargs['indent'] = 2 if current_app.debug else None
        return json.dumps(obj, **kwargs)
    
    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

def create_app():
    logger.info("=" * 60)
    logger.info("正在创建 Flask 应用...")
    logger.info("=" * 60)
    
    # 输出配置摘要
    logger.info(f"应用配置摘要:")
    logger.info(f"  环境: {settings.app.environment}")
    logger.info(f"  调试模式: {settings.app.debug}")
    logger.info(f"  端口: {settings.app.port}")
    logger.info(f"  数据库: {settings._mask_password(settings.database.url)}")
    logger.info(f"  GitLab: {settings.gitlab.url}")
    logger.info(f"  LDAP 认证: {'启用' if settings.ldap.enabled else '禁用'}")
    logger.info(f"  日志级别: {settings.logging.level}")
    logger.info("=" * 60)
    
    app = Flask(__name__)
    app.json = InternationalJSONProvider(app)
    
    # 初始化日志中间件（会自动注册请求钩子）
    LoggingMiddleware(app)
    logger.info("日志中间件已初始化")
    
    # 初始化数据库（仅在需要时）
    if settings.app.init_db:
        logger.info("正在初始化数据库...")
        initialize_database()
        logger.info("数据库初始化完成")
    
    # Setup API routes - 使用新的 Blueprint 注册中心
    logger.info("正在注册 API Blueprints...")
    register_blueprints(app)
    logger.info("API Blueprints 注册完成")
    
    # 启动监控调度器
    try:
        logger.info("正在启动监控调度器...")
        monitoring_scheduler.start()
        logger.info("监控调度器启动完成")
    except Exception as e:
        logger.error(f"启动监控调度器失败: {e}")
        # 即使调度器启动失败，也继续运行应用
    
    # Serve frontend static files
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        import os
        from flask import send_from_directory
        static_folder = os.path.join(app.root_path, 'static')
        if path and os.path.exists(os.path.join(static_folder, path)):
            return send_from_directory(static_folder, path)
        else:
            return send_from_directory(static_folder, 'index.html')
    
    logger.info("Flask 应用创建完成")
    logger.info("=" * 60)
    return app

if __name__ == "__main__":
    app = create_app()
    
    logger.info(f"启动 GitLab Insight API 服务...")
    logger.info(f"监听地址: {settings.app.host}:{settings.app.port}")
    logger.info(f"调试模式: {settings.app.debug}")
    
    print(f"\n{'=' * 60}")
    print(f"GitLab Insight API Server")
    print(f"{'=' * 60}")
    print(f"Environment: {settings.app.environment}")
    print(f"Address:     http://{settings.app.host}:{settings.app.port}")
    print(f"Debug Mode:  {settings.app.debug}")
    print(f"{'=' * 60}\n")
    
    app.run(
        host=settings.app.host,
        port=settings.app.port,
        debug=settings.app.debug
    )