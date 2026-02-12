from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from .base_dto import DataTransformMixin

@dataclass
class ApiAccessLogData(DataTransformMixin):
    """API 访问日志数据 DTO"""
    id: int
    access_time: str
    client_ip: str
    http_method: str
    api_path: str
    http_status: int
    response_size: Optional[int]
    user_agent: Optional[str]
    response_time: Optional[float]
    
    @classmethod
    def from_model(cls, log_model) -> 'ApiAccessLogData':
        """从数据库模型创建 DTO"""
        return cls(
            id=log_model.id,
            access_time=log_model.access_time.isoformat(),
            client_ip=log_model.client_ip,
            http_method=log_model.http_method,
            api_path=log_model.api_path,
            http_status=log_model.http_status,
            response_size=log_model.response_size,
            user_agent=log_model.user_agent,
            response_time=log_model.response_time
        )