from typing import Optional, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class BaseResult:
    """基础操作结果 DTO"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Any] = None  # 添加 data 字段用于携带额外数据
    
    @classmethod
    def create_success(cls, message: str = "Operation completed successfully", data: Any = None) -> 'BaseResult':
        """创建成功结果"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def create_failure(cls, error: str) -> 'BaseResult':
        """创建失败结果"""
        return cls(success=False, error=error)

@dataclass
class CountableResult(BaseResult):
    """可计数的操作结果 DTO"""
    count: int = 0
    
    @classmethod
    def create_success(cls, count: int, message: str = None, data: Any = None) -> 'CountableResult':
        """创建成功结果"""
        default_message = f"Successfully processed {count} items"
        return cls(success=True, count=count, message=message or default_message, data=data)
    
    @classmethod
    def create_failure(cls, error: str) -> 'CountableResult':
        """创建失败结果"""
        return cls(success=False, count=0, error=error)

@dataclass
class SyncResult(CountableResult):
    """同步操作结果 DTO"""
    total_found: int = 0
    
    @classmethod
    def create_success(cls, synced_count: int, total_found: int, message: str = None) -> 'SyncResult':
        """创建成功的同步结果"""
        default_message = f"Successfully synced {synced_count}/{total_found} items"
        return cls(
            success=True,
            count=synced_count,
            total_found=total_found,
            message=message or default_message
        )

@dataclass
class StatisticsBase:
    """基础统计信息 DTO"""
    total: int = 0
    
    def get_percentage(self, value: int) -> float:
        """计算百分比"""
        if self.total == 0:
            return 0.0
        return (value / self.total) * 100

class DataTransformMixin:
    """数据转换混入类"""
    
    @classmethod
    @abstractmethod
    def from_model(cls, model: Any) -> 'DataTransformMixin':
        """从模型对象创建 DTO"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        if hasattr(self, '__dict__'):
            return self.__dict__
        return {}