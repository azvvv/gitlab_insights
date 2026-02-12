'''
Author: yang_x_neu azvvv2023@outlook.com
Date: 2025-06-13 16:13:10
LastEditors: yang_x_neu azvvv2023@outlook.com
LastEditTime: 2025-06-16 13:29:25
FilePath: \gitlab_insight\src\database\connection.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from config.settings import settings

# 使用统一配置管理
engine = create_engine(
    settings.database.url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    echo=settings.database.echo
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_connection():
    """返回数据库会话对象"""
    return SessionLocal()

@contextmanager
def get_db_session():
    """上下文管理器，自动管理会话生命周期"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_engine():
    """返回数据库引擎"""
    return engine

def initialize_database():
    """初始化数据库表"""
    from database.models import create_tables
    create_tables(engine)
    print("Database tables created successfully")