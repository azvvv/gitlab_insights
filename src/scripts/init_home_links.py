"""
执行 home_links 表的创建脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent  # 向上两级到项目根目录
sys.path.insert(0, str(project_root / 'src'))

from database.connection import get_db_session

def execute_sql_file():
    """执行 SQL 文件"""
    sql_file = project_root / 'sql' / 'create_home_links.sql'
    
    if not sql_file.exists():
        print(f"错误: SQL 文件不存在: {sql_file}")
        return False
    
    print(f"正在读取 SQL 文件: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割 SQL 语句
    sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    print(f"找到 {len(sql_statements)} 条 SQL 语句")
    
    # 执行 SQL
    from sqlalchemy import text
    
    with get_db_session() as db:
        try:
            for i, stmt in enumerate(sql_statements, 1):
                if stmt.strip():
                    print(f"执行语句 {i}/{len(sql_statements)}...")
                    db.execute(text(stmt))
            
            db.commit()
            print("✅ SQL 文件执行成功！")
            
            # 验证数据
            result = db.execute(text("SELECT COUNT(*) FROM home_links"))
            count = result.scalar()
            print(f"✅ home_links 表已创建，包含 {count} 条记录")
            
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ 执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    execute_sql_file()
