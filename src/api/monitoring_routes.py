"""
监控服务 API

包含以下功能：
- 监控指标查询（metrics, trend, summary）
- 调度器管理
"""

from flask import Blueprint
from datetime import datetime
from services.monitoring_service import monitoring_service
from services.scheduler import monitoring_scheduler
from api.response import api_response
from api.auth_decorators import token_required
from utils.validators import get_request_params
from utils.errorhandler import handle_exceptions

monitoring_bp = Blueprint('monitoring', __name__)


# ==================== 监控指标查询 ====================

@monitoring_bp.route('/metrics', methods=['GET'])
@token_required
@handle_exceptions
def get_monitoring_metrics():
    """查询监控指标数据"""
    params = get_request_params({
        'application': {'type': str, 'required': False},
        'metric_type': {'type': str, 'required': False},
        'start_date': {'type': str, 'required': False},
        'end_date': {'type': str, 'required': False},
        'limit': {'type': int, 'default': 100}
    })
    
    try:
        # 转换日期字符串
        start_date = None
        end_date = None
        
        if params.get('start_date'):
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d').date()
        if params.get('end_date'):
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d').date()
        
        metrics = monitoring_service.get_metrics(
            application=params.get('application'),
            metric_type=params.get('metric_type'),
            start_date=start_date,
            end_date=end_date,
            limit=params.get('limit', 100)
        )
        
        return api_response(
            success=True,
            metrics=[m.to_dict() for m in metrics],
            count=len(metrics)
        )
    except Exception as e:
        return api_response(
            success=False,
            error=f'查询监控指标失败: {str(e)}',
            status_code=500
        )


@monitoring_bp.route('/metrics/latest', methods=['GET'])
@token_required
@handle_exceptions
def get_latest_metric():
    """获取最新的监控指标"""
    params = get_request_params({
        'application': {'type': str, 'required': True},
        'metric_type': {'type': str, 'required': True}
    })
    
    try:
        metric = monitoring_service.get_latest_metric(
            application=params['application'],
            metric_type=params['metric_type']
        )
        
        if metric:
            return api_response(
                success=True,
                metric=metric.to_dict()
            )
        else:
            return api_response(
                success=False,
                error='未找到指标数据',
                status_code=404
            )
    except Exception as e:
        return api_response(
            success=False,
            error=f'获取最新指标失败: {str(e)}',
            status_code=500
        )


@monitoring_bp.route('/metrics/trend', methods=['GET'])
@token_required
@handle_exceptions
def get_metric_trend():
    """获取监控指标趋势"""
    params = get_request_params({
        'application': {'type': str, 'required': True},
        'metric_type': {'type': str, 'required': True},
        'days': {'type': int, 'default': 30}
    })
    
    try:
        metrics = monitoring_service.get_metric_trend(
            application=params['application'],
            metric_type=params['metric_type'],
            days=params.get('days', 30)
        )
        
        return api_response(
            success=True,
            metrics=[m.to_dict() for m in metrics],
            count=len(metrics)
        )
    except Exception as e:
        return api_response(
            success=False,
            error=f'获取趋势数据失败: {str(e)}',
            status_code=500
        )


@monitoring_bp.route('/applications/<string:application>/summary', methods=['GET'])
@token_required
@handle_exceptions
def get_application_summary(application):
    """获取应用的监控摘要"""
    try:
        summary = monitoring_service.get_application_summary(application)
        return api_response(
            success=True,
            summary=summary
        )
    except Exception as e:
        return api_response(
            success=False,
            error=f'获取应用摘要失败: {str(e)}',
            status_code=500
        )


# ==================== 调度器管理 ====================

@monitoring_bp.route('/scheduler/status', methods=['GET'])
@token_required
@handle_exceptions
def get_scheduler_status():
    """获取调度器状态"""
    try:
        jobs_status = monitoring_scheduler.get_jobs_status()
        return api_response(
            success=True,
            running=monitoring_scheduler.scheduler.running,
            jobs=jobs_status,
            count=len(jobs_status)
        )
    except Exception as e:
        return api_response(
            success=False,
            error=f'获取调度器状态失败: {str(e)}',
            status_code=500
        )


@monitoring_bp.route('/scheduler/jobs/<string:job_id>/run', methods=['POST'])
@token_required
@handle_exceptions
def run_scheduler_job(job_id):
    """手动执行调度任务"""
    try:
        success = monitoring_scheduler.run_job_now(job_id)
        if success:
            return api_response(
                success=True,
                message=f'任务 {job_id} 执行成功'
            )
        else:
            return api_response(
                success=False,
                error=f'未找到任务: {job_id}',
                status_code=404
            )
    except Exception as e:
        return api_response(
            success=False,
            error=f'执行任务失败: {str(e)}',
            status_code=500
        )
