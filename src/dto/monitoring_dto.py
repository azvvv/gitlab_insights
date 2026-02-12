"""
监控数据传输对象模块

提供监控指标数据的数据传输对象定义。
"""

from datetime import date, datetime
from typing import Optional, Any, Dict


class MonitoringMetricDTO:
    """监控指标数据传输对象"""
    
    def __init__(
        self,
        id: Optional[int] = None,
        metric_date: Optional[date] = None,
        metric_timestamp: Optional[datetime] = None,
        application: Optional[str] = None,
        metric_type: Optional[str] = None,
        metric_value: Optional[float] = None,
        metric_value_int: Optional[int] = None,
        metric_value_text: Optional[str] = None,
        metric_unit: Optional[str] = None,
        metric_metadata: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
        data_source: Optional[str] = None,
        collection_method: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.metric_date = metric_date
        self.metric_timestamp = metric_timestamp
        self.application = application
        self.metric_type = metric_type
        self.metric_value = metric_value
        self.metric_value_int = metric_value_int
        self.metric_value_text = metric_value_text
        self.metric_unit = metric_unit
        self.metric_metadata = metric_metadata or {}
        self.status = status
        self.error_message = error_message
        self.data_source = data_source
        self.collection_method = collection_method
        self.created_at = created_at
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'metric_date': self.metric_date.isoformat() if self.metric_date else None,
            'metric_timestamp': self.metric_timestamp.isoformat() if self.metric_timestamp else None,
            'application': self.application,
            'metric_type': self.metric_type,
            'metric_value': self.metric_value,
            'metric_value_int': self.metric_value_int,
            'metric_value_text': self.metric_value_text,
            'metric_unit': self.metric_unit,
            'metric_metadata': self.metric_metadata,
            'status': self.status,
            'error_message': self.error_message,
            'data_source': self.data_source,
            'collection_method': self.collection_method,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_model(cls, model):
        """从数据库模型创建 DTO"""
        if model is None:
            return None
        
        return cls(
            id=model.id,
            metric_date=model.metric_date,
            metric_timestamp=model.metric_timestamp,
            application=model.application,
            metric_type=model.metric_type,
            metric_value=model.metric_value,
            metric_value_int=model.metric_value_int,
            metric_value_text=model.metric_value_text,
            metric_unit=model.metric_unit,
            metric_metadata=model.metric_metadata,
            status=model.status,
            error_message=model.error_message,
            data_source=model.data_source,
            collection_method=model.collection_method,
            created_at=model.created_at
        )


class MonitoringQueryDTO:
    """监控数据查询参数 DTO"""
    
    def __init__(
        self,
        application: Optional[str] = None,
        metric_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 100
    ):
        self.application = application
        self.metric_type = metric_type
        self.start_date = start_date
        self.end_date = end_date
        self.page = page
        self.page_size = page_size
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'application': self.application,
            'metric_type': self.metric_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'page': self.page,
            'page_size': self.page_size
        }
