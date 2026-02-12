from datetime import datetime, date
from typing import List, Optional
from dataclasses import dataclass
from .base_dto import BaseResult, CountableResult

@dataclass
class ImportStatusSummary:
    """导入状态摘要 DTO"""
    total_records: int
    min_date: Optional[date]
    max_date: Optional[date] 
    import_days: int
    imported_dates: List[str]
    
    @classmethod
    def create_empty(cls) -> 'ImportStatusSummary':
        """创建空的状态摘要"""
        return cls(
            total_records=0,
            min_date=None,
            max_date=None,
            import_days=0,
            imported_dates=[]
        )

@dataclass
class ImportDetail:
    """导入详情 DTO"""
    import_date: str
    record_count: int
    import_time: str
    log_file_path: Optional[str]
    is_complete: bool

@dataclass
class ImportResult(CountableResult):
    """导入结果 DTO"""
    imported_dates: List[date] = None
    already_imported_dates: List[date] = None
    
    def __post_init__(self):
        if self.imported_dates is None:
            self.imported_dates = []
        if self.already_imported_dates is None:
            self.already_imported_dates = []
    
    @classmethod
    def create_success(cls, imported_count: int, total_found: int, imported_dates: List[date]) -> 'ImportResult':
        """创建成功的导入结果"""
        return cls(
            success=True,
            count=imported_count,
            imported_dates=imported_dates,
            message=f"Successfully imported {imported_count} records from {len(imported_dates)} dates"
        )
    
    @classmethod
    def create_already_imported(cls, total_records: int, already_imported_dates: List[date]) -> 'ImportResult':
        """创建已导入的结果"""
        return cls(
            success=False,
            count=0,
            already_imported_dates=already_imported_dates,
            message=f"Data for {len(already_imported_dates)} dates already imported ({total_records} records)"
        )
    
    @classmethod
    def create_no_data(cls) -> 'ImportResult':
        """创建无数据的结果"""
        return cls(
            success=False,
            count=0,
            message="No data found to import"
        )
    
    @classmethod
    def create_file_not_found(cls, file_path: str) -> 'ImportResult':
        """创建文件未找到的结果"""
        return cls(
            success=False,
            count=0,
            error=f"Log file not found: {file_path}"
        )
    
    @classmethod
    def create_failure(cls, error: str) -> 'ImportResult':
        """创建失败的结果"""
        return cls(
            success=False,
            count=0,
            error=error
        )