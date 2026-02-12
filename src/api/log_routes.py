"""
日志管理 API

包含以下功能：
- 日志解析
- 导入状态查询
- 导入历史记录
- 日志数据查询
"""

from flask import Blueprint, request
import os
from services.log_parser import LogParser
from services.database_service import DatabaseService
from api.response import api_response
from utils.validators import get_request_params
from utils.errorhandler import handle_exceptions

log_bp = Blueprint('log', __name__)


@log_bp.route('/parse', methods=['POST'])
@handle_exceptions
def parse_log():
    """触发日志解析"""
    data = request.get_json() if request.is_json else {}
    log_file_path = data.get('log_file') if data and data.get('log_file') else os.environ.get('LOG_FILE_PATH')
    
    if not log_file_path:
        return api_response(success=False, error='Log file path not provided', status_code=400)

    log_parser = LogParser(log_file_path)
    parse_result = log_parser.parse()
    
    # 修复：直接处理 ImportResult 对象，不使用 handle_service_result
    if not parse_result.success:
        return api_response(success=False, error=parse_result.message, status_code=400)
    
    # 返回解析结果
    return api_response(
        success=True,
        message=parse_result.message,
        imported_count=parse_result.count,
        imported_dates=[str(date) for date in parse_result.imported_dates] if parse_result.imported_dates else [],
        already_imported_dates=[str(date) for date in parse_result.already_imported_dates] if parse_result.already_imported_dates else []
    )


@log_bp.route('/status', methods=['GET'])
@handle_exceptions
def get_status():
    """获取导入状态（从状态表读取）"""
    db_service = DatabaseService()
    status_summary = db_service.get_import_status_summary()
    
    return api_response(
        total_records=status_summary.total_records,
        import_days=status_summary.import_days,
        date_range={
            'min_date': str(status_summary.min_date) if status_summary.min_date else None,
            'max_date': str(status_summary.max_date) if status_summary.max_date else None
        },
        imported_dates=status_summary.imported_dates
    )


@log_bp.route('/import-history', methods=['GET'])
@handle_exceptions
def get_import_history():
    """获取详细的导入历史"""
    db_service = DatabaseService()
    import_details = db_service.get_import_details()
    
    # 将 ImportDetail 对象转换为字典
    import_history = [
        {
            'log_date': detail.import_date,
            'record_count': detail.record_count,
            'import_time': detail.import_time,
            'log_file_path': detail.log_file_path,
            'is_complete': detail.is_complete,
            'status': 'success' if detail.is_complete else 'pending'
        }
        for detail in import_details
    ]
    
    return api_response(
        import_history=import_history,
        total_imports=len(import_history)
    )


@log_bp.route('/logs', methods=['GET'])
@handle_exceptions
def get_logs():
    """获取日志数据"""
    params = get_request_params({
        'limit': {'type': int, 'default': 100}
    })
    
    db_service = DatabaseService()
    logs = db_service.get_logs(limit=params['limit'])
    
    return api_response(
        logs=logs,
        count=len(logs),
        total_records=db_service.get_total_count()
    )
