"""
数据序列化工具
用于将 ORM 对象、数据库模型等转换为 JSON 可序列化的格式
"""
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict, is_dataclass


class ModelSerializer:
    """
    统一的模型序列化工具
    
    提供智能序列化功能，支持：
    1. Model.to_dict() 方法
    2. Dataclass 对象
    3. SQLAlchemy ORM 对象
    4. 普通对象
    """
    
    @staticmethod
    def serialize(obj: Any) -> Optional[Dict[str, Any]]:
        """
        智能序列化对象为字典
        
        优先级：
        1. 如果对象有 to_dict() 方法，使用之
        2. 如果是 dataclass，使用 asdict()
        3. 如果是 SQLAlchemy ORM 对象，提取列属性
        4. 否则提取 __dict__ 属性
        
        Args:
            obj: 要序列化的对象
            
        Returns:
            序列化后的字典，如果对象为 None 则返回 None
            
        Example:
            >>> user = db.query(User).first()
            >>> user_dict = ModelSerializer.serialize(user)
            >>> # {'id': 1, 'username': 'admin', 'created_at': '2026-02-05T10:30:00'}
        """
        if obj is None:
            return None
        
        # 方式1：对象自带 to_dict() 方法（优先级最高）
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            try:
                return obj.to_dict()
            except Exception as e:
                print(f"Warning: to_dict() failed for {type(obj).__name__}: {e}")
                # 继续尝试其他方式
        
        # 方式2：dataclass 对象
        if is_dataclass(obj):
            try:
                return asdict(obj)
            except Exception as e:
                print(f"Warning: asdict() failed for {type(obj).__name__}: {e}")
        
        # 方式3：SQLAlchemy ORM 对象
        if hasattr(obj, '__table__'):
            return ModelSerializer._serialize_orm_object(obj)
        
        # 方式4：普通对象
        if hasattr(obj, '__dict__'):
            return ModelSerializer._serialize_dict(obj.__dict__)
        
        # 无法序列化，返回字符串表示
        return {'_value': str(obj), '_type': type(obj).__name__}
    
    @staticmethod
    def serialize_many(objects: List[Any]) -> List[Dict[str, Any]]:
        """
        批量序列化对象列表
        
        Args:
            objects: 对象列表
            
        Returns:
            序列化后的字典列表
            
        Example:
            >>> users = db.query(User).all()
            >>> users_list = ModelSerializer.serialize_many(users)
        """
        return [ModelSerializer.serialize(obj) for obj in objects if obj is not None]
    
    @staticmethod
    def _serialize_orm_object(obj: Any) -> Dict[str, Any]:
        """
        序列化 SQLAlchemy ORM 对象
        
        Args:
            obj: SQLAlchemy ORM 对象
            
        Returns:
            序列化后的字典
        """
        result = {}
        
        try:
            # 提取所有列属性
            for column in obj.__table__.columns:
                value = getattr(obj, column.name)
                result[column.name] = ModelSerializer._serialize_value(value)
        except Exception as e:
            print(f"Warning: Failed to serialize ORM object {type(obj).__name__}: {e}")
            # 降级到 __dict__
            return ModelSerializer._serialize_dict(obj.__dict__)
        
        return result
    
    @staticmethod
    def _serialize_dict(data: Dict) -> Dict[str, Any]:
        """
        序列化字典，处理特殊类型
        
        Args:
            data: 原始字典
            
        Returns:
            序列化后的字典
        """
        result = {}
        
        for key, value in data.items():
            # 跳过私有属性和 SQLAlchemy 内部属性
            if key.startswith('_'):
                continue
            
            result[key] = ModelSerializer._serialize_value(value)
        
        return result
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """
        序列化单个值
        
        Args:
            value: 要序列化的值
            
        Returns:
            序列化后的值
        """
        # None
        if value is None:
            return None
        
        # datetime 和 date 对象
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        
        # 递归序列化嵌套对象
        if hasattr(value, 'to_dict') and callable(value.to_dict):
            return value.to_dict()
        
        if is_dataclass(value):
            return asdict(value)
        
        if hasattr(value, '__table__'):
            return ModelSerializer._serialize_orm_object(value)
        
        # 基本类型直接返回
        if isinstance(value, (str, int, float, bool)):
            return value
        
        # 列表和元组
        if isinstance(value, (list, tuple)):
            return [ModelSerializer._serialize_value(item) for item in value]
        
        # 字典
        if isinstance(value, dict):
            return {k: ModelSerializer._serialize_value(v) for k, v in value.items()}
        
        # 其他类型转为字符串
        return str(value)


# ============================================================================
# 以下是向后兼容的函数，保留原有的函数签名
# 建议使用 ModelSerializer 类的静态方法
# ============================================================================

def serialize_orm_object(obj: Any) -> Optional[Dict]:
    """
    序列化 SQLAlchemy ORM 对象为字典
    
    已废弃：建议使用 ModelSerializer.serialize() 替代
    
    Args:
        obj: SQLAlchemy ORM 对象
    
    Returns:
        序列化后的字典，如果对象为 None 则返回 None
    
    Example:
        >>> user = session.query(User).first()
        >>> user_dict = serialize_orm_object(user)
        >>> # {'id': 1, 'username': 'admin', 'created_at': '2025-01-05T10:30:45'}
    """
    return ModelSerializer.serialize(obj)


def serialize_orm_list(objects: List[Any]) -> List[Dict]:
    """
    序列化 ORM 对象列表
    
    已废弃：建议使用 ModelSerializer.serialize_many() 替代
    
    Args:
        objects: ORM 对象列表
    
    Returns:
        序列化后的字典列表
    
    Example:
        >>> users = session.query(User).all()
        >>> users_list = serialize_orm_list(users)
        >>> # [{'id': 1, 'username': 'admin'}, {'id': 2, 'username': 'user'}]
    """
    return ModelSerializer.serialize_many(objects)


def serialize_dataclass(obj: Any) -> Optional[Dict]:
    """
    序列化 dataclass 对象为字典
    
    已废弃：建议使用 ModelSerializer.serialize() 替代
    
    Args:
        obj: dataclass 对象
    
    Returns:
        序列化后的字典
    """
    return ModelSerializer.serialize(obj)


def serialize_mixed_list(objects: List[Any]) -> List[Dict]:
    """
    序列化混合类型对象列表（支持 ORM、dataclass 等）
    
    已废弃：建议使用 ModelSerializer.serialize_many() 替代
    
    Args:
        objects: 对象列表
    
    Returns:
        序列化后的字典列表
    """
    return ModelSerializer.serialize_many(objects)
