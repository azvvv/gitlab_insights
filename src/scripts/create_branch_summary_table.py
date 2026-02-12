"""
数据库迁移脚本 - 创建分支汇总统计表

创建 gitlab_branch_summary 表用于存储分支统计数据
优化前端查询性能

运行方式:
    python scripts/create_branch_summary_table.py
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.models import Base, GitlabBranchSummary
from database.connection import engine
from services.gitlab_service import GitlabService
from utils.logger import get_logger

logger = get_logger(__name__)


def create_branch_summary_table():
    """创建分支汇总统计表"""
    try:
        logger.info("开始创建 gitlab_branch_summary 表...")
        
        # 只创建 GitlabBranchSummary 表
        GitlabBranchSummary.__table__.create(bind=engine, checkfirst=True)
        
        logger.info("✅ gitlab_branch_summary 表创建成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建表失败: {e}")
        logger.exception(e)
        return False


def generate_initial_data():
    """为现有仓库生成初始汇总数据"""
    try:
        logger.info("开始生成初始分支汇总数据...")
        
        gitlab_service = GitlabService()
        result = gitlab_service.generate_branch_summaries(force_refresh=True)
        
        if result['success']:
            logger.info(f"✅ 初始数据生成成功: {result['message']}")
            logger.info(f"   - 总仓库数: {result['total_repositories']}")
            logger.info(f"   - 成功: {result['success_count']}")
            logger.info(f"   - 失败: {result['error_count']}")
            return True
        else:
            logger.error(f"❌ 初始数据生成失败: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 生成初始数据失败: {e}")
        logger.exception(e)
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("GitLab 分支汇总表创建脚本")
    print("=" * 60)
    print()
    
    # 步骤1: 创建表
    print("步骤 1/2: 创建数据库表")
    if not create_branch_summary_table():
        print("\n❌ 表创建失败，请检查日志")
        return 1
    
    print()
    
    # 步骤2: 生成初始数据
    print("步骤 2/2: 生成初始数据")
    user_input = input("是否为现有仓库生成初始汇总数据？(y/n): ").strip().lower()
    
    if user_input == 'y':
        if not generate_initial_data():
            print("\n⚠️  初始数据生成失败，但表已创建成功")
            print("   您可以稍后通过 API 或脚本手动生成数据")
            return 1
    else:
        print("跳过初始数据生成")
        print("提示: 您可以稍后通过以下方式生成数据:")
        print("  - API: POST /api/gitlab/branches/summary/generate")
        print("  - 脚本: python scripts/generate_branch_summary.py")
    
    print()
    print("=" * 60)
    print("✅ 迁移完成！")
    print("=" * 60)
    print()
    print("可用的 API 接口:")
    print("  - GET  /api/gitlab/branches/summary          - 获取所有汇总")
    print("  - GET  /api/gitlab/branches/summary/global   - 获取全局统计")
    print("  - GET  /api/gitlab/branches/summary/repository/{id} - 获取单个仓库汇总")
    print("  - POST /api/gitlab/branches/summary/generate - 生成所有汇总（异步）")
    print()
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
