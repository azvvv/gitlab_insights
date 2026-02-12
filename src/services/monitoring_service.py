"""
监控数据服务模块

提供监控指标数据的存储、查询和统计功能。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from database.connection import get_db_session
from database.models import MonitoringMetric
from dto.monitoring_dto import MonitoringMetricDTO, MonitoringQueryDTO

logger = logging.getLogger(__name__)


class MonitoringService:
    """监控数据服务类"""
    
    def save_metric(
        self,
        application: str,
        metric_type: str,
        metric_value: Optional[float] = None,
        metric_value_int: Optional[int] = None,
        metric_value_text: Optional[str] = None,
        metric_unit: Optional[str] = None,
        metric_metadata: Optional[Dict[str, Any]] = None,
        metric_date: Optional[date] = None,
        data_source: Optional[str] = None,
        collection_method: str = 'api',
        status: str = 'success',
        error_message: Optional[str] = None
    ) -> MonitoringMetricDTO:
        """
        保存监控指标数据
        
        Args:
            application: 应用名称
            metric_type: 指标类型
            metric_value: 数值型指标值
            metric_value_int: 整数型指标值
            metric_value_text: 文本型指标值
            metric_unit: 指标单位
            metric_metadata: 扩展元数据
            metric_date: 指标日期（默认为当天）
            data_source: 数据源
            collection_method: 采集方式
            status: 采集状态
            error_message: 错误信息
        
        Returns:
            MonitoringMetricDTO: 保存的监控指标数据
        """
        session: Session = get_db_session()
        try:
            if metric_date is None:
                metric_date = date.today()
            
            # 检查当天是否已有该指标的记录
            existing = session.query(MonitoringMetric).filter(
                and_(
                    MonitoringMetric.metric_date == metric_date,
                    MonitoringMetric.application == application,
                    MonitoringMetric.metric_type == metric_type
                )
            ).first()
            
            if existing:
                # 更新现有记录
                existing.metric_value = metric_value
                existing.metric_value_int = metric_value_int
                existing.metric_value_text = metric_value_text
                existing.metric_unit = metric_unit
                existing.metric_metadata = metric_metadata or {}
                existing.metric_timestamp = datetime.now()
                existing.status = status
                existing.error_message = error_message
                existing.data_source = data_source
                existing.collection_method = collection_method
                
                session.commit()
                logger.info(f"更新监控指标: {application}.{metric_type} ({metric_date})")
                return MonitoringMetricDTO.from_model(existing)
            else:
                # 创建新记录
                metric = MonitoringMetric(
                    metric_date=metric_date,
                    metric_timestamp=datetime.now(),
                    application=application,
                    metric_type=metric_type,
                    metric_value=metric_value,
                    metric_value_int=metric_value_int,
                    metric_value_text=metric_value_text,
                    metric_unit=metric_unit,
                    metric_metadata=metric_metadata or {},
                    status=status,
                    error_message=error_message,
                    data_source=data_source,
                    collection_method=collection_method
                )
                
                session.add(metric)
                session.commit()
                logger.info(f"保存监控指标: {application}.{metric_type} ({metric_date})")
                return MonitoringMetricDTO.from_model(metric)
                
        except Exception as e:
            session.rollback()
            logger.error(f"保存监控指标失败: {e}")
            raise
        finally:
            session.close()
    
    def get_metrics(
        self,
        application: Optional[str] = None,
        metric_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[MonitoringMetricDTO]:
        """
        查询监控指标数据
        
        Args:
            application: 应用名称（可选）
            metric_type: 指标类型（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 返回数量限制
        
        Returns:
            List[MonitoringMetricDTO]: 监控指标数据列表
        """
        session: Session = get_db_session()
        try:
            query = session.query(MonitoringMetric)
            
            # 添加过滤条件
            if application:
                query = query.filter(MonitoringMetric.application == application)
            if metric_type:
                query = query.filter(MonitoringMetric.metric_type == metric_type)
            if start_date:
                query = query.filter(MonitoringMetric.metric_date >= start_date)
            if end_date:
                query = query.filter(MonitoringMetric.metric_date <= end_date)
            
            # 按日期降序排序
            query = query.order_by(MonitoringMetric.metric_date.desc())
            
            # 限制返回数量
            query = query.limit(limit)
            
            metrics = query.all()
            return [MonitoringMetricDTO.from_model(m) for m in metrics]
            
        except Exception as e:
            logger.error(f"查询监控指标失败: {e}")
            raise
        finally:
            session.close()
    
    def get_latest_metric(
        self,
        application: str,
        metric_type: str
    ) -> Optional[MonitoringMetricDTO]:
        """
        获取最新的监控指标
        
        Args:
            application: 应用名称
            metric_type: 指标类型
        
        Returns:
            Optional[MonitoringMetricDTO]: 最新的监控指标数据，如果不存在则返回 None
        """
        session: Session = get_db_session()
        try:
            metric = session.query(MonitoringMetric).filter(
                and_(
                    MonitoringMetric.application == application,
                    MonitoringMetric.metric_type == metric_type
                )
            ).order_by(MonitoringMetric.metric_date.desc()).first()
            
            if metric:
                return MonitoringMetricDTO.from_model(metric)
            return None
            
        except Exception as e:
            logger.error(f"获取最新监控指标失败: {e}")
            raise
        finally:
            session.close()
    
    def get_metric_trend(
        self,
        application: str,
        metric_type: str,
        days: int = 30
    ) -> List[MonitoringMetricDTO]:
        """
        获取监控指标趋势数据
        
        Args:
            application: 应用名称
            metric_type: 指标类型
            days: 天数（默认30天）
        
        Returns:
            List[MonitoringMetricDTO]: 趋势数据列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        return self.get_metrics(
            application=application,
            metric_type=metric_type,
            start_date=start_date,
            end_date=end_date,
            limit=days
        )
    
    def get_application_summary(self, application: str) -> Dict[str, Any]:
        """
        获取应用的监控摘要
        
        Args:
            application: 应用名称
        
        Returns:
            Dict[str, Any]: 监控摘要数据
        """
        session: Session = get_db_session()
        try:
            # 获取所有指标类型
            metric_types = session.query(
                MonitoringMetric.metric_type
            ).filter(
                MonitoringMetric.application == application
            ).distinct().all()
            
            summary = {
                'application': application,
                'metrics': []
            }
            
            for (metric_type,) in metric_types:
                # 获取最新数据
                latest = self.get_latest_metric(application, metric_type)
                if latest:
                    summary['metrics'].append({
                        'type': metric_type,
                        'latest_value': latest.metric_value_int or latest.metric_value or latest.metric_value_text,
                        'unit': latest.metric_unit,
                        'date': latest.metric_date.isoformat() if latest.metric_date else None,
                        'status': latest.status
                    })
            
            return summary
            
        except Exception as e:
            logger.error(f"获取应用监控摘要失败: {e}")
            raise
        finally:
            session.close()
    
    def delete_old_metrics(self, days: int = 365) -> int:
        """
        删除过期的监控数据
        
        Args:
            days: 保留天数（默认365天）
        
        Returns:
            int: 删除的记录数
        """
        session: Session = get_db_session()
        try:
            cutoff_date = date.today() - timedelta(days=days)
            
            deleted = session.query(MonitoringMetric).filter(
                MonitoringMetric.metric_date < cutoff_date
            ).delete()
            
            session.commit()
            logger.info(f"删除了 {deleted} 条过期监控数据（早于 {cutoff_date}）")
            return deleted
            
        except Exception as e:
            session.rollback()
            logger.error(f"删除过期监控数据失败: {e}")
            raise
        finally:
            session.close()


# 创建全局监控服务实例
monitoring_service = MonitoringService()
