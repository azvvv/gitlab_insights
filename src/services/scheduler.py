"""
调度器模块

提供定时任务调度功能，用于自动采集监控数据。
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from config.settings import settings
from services.monitoring_service import monitoring_service

logger = logging.getLogger(__name__)


class MonitoringScheduler:
    """监控数据调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.scheduler = BackgroundScheduler(
            timezone='Asia/Shanghai',
            job_defaults={
                'coalesce': True,  # 合并错过的执行
                'max_instances': 1  # 每个任务最多只运行一个实例
            }
        )
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """设置事件监听器"""
        def job_executed(event):
            """任务执行成功回调"""
            logger.info(f"定时任务执行成功: {event.job_id}")
        
        def job_error(event):
            """任务执行失败回调"""
            logger.error(f"定时任务执行失败: {event.job_id}, 异常: {event.exception}")
        
        self.scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(job_error, EVENT_JOB_ERROR)
    
    def cleanup_old_metrics_job(self):
        """清理过期监控数据的定时任务"""
        try:
            logger.info("开始执行监控数据清理任务...")
            
            # 保留365天的数据
            deleted_count = monitoring_service.delete_old_metrics(days=365)
            logger.info(f"监控数据清理完成，删除了 {deleted_count} 条记录")
            
        except Exception as e:
            logger.error(f"监控数据清理任务执行失败: {e}", exc_info=True)
    
    def add_jobs(self):
        """添加所有定时任务"""
        # 监控数据清理任务 - 每周日凌晨3点执行
        self.scheduler.add_job(
            func=self.cleanup_old_metrics_job,
            trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
            id='monitoring_data_cleanup',
            name='监控数据清理',
            replace_existing=True
        )
        logger.info("已添加定时任务: 监控数据清理 (每周日 03:00)")
    
    def start(self):
        """启动调度器"""
        try:
            if not self.scheduler.running:
                self.add_jobs()
                self.scheduler.start()
                logger.info("监控调度器已启动")
                
                # 列出所有任务
                jobs = self.scheduler.get_jobs()
                logger.info(f"当前活跃的定时任务数: {len(jobs)}")
                for job in jobs:
                    logger.info(f"  - {job.name} (ID: {job.id})")
            else:
                logger.warning("监控调度器已经在运行中")
        except Exception as e:
            logger.error(f"启动监控调度器失败: {e}", exc_info=True)
            raise
    
    def stop(self):
        """停止调度器"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("监控调度器已停止")
            else:
                logger.warning("监控调度器未在运行")
        except Exception as e:
            logger.error(f"停止监控调度器失败: {e}", exc_info=True)
    
    def get_jobs_status(self):
        """获取所有任务状态"""
        jobs = self.scheduler.get_jobs()
        status = []
        
        for job in jobs:
            status.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return status
    
    def run_job_now(self, job_id: str):
        """立即运行指定任务"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.func()
                logger.info(f"手动执行任务成功: {job_id}")
                return True
            else:
                logger.warning(f"未找到任务: {job_id}")
                return False
        except Exception as e:
            logger.error(f"手动执行任务失败: {job_id}, 错误: {e}", exc_info=True)
            raise


# 创建全局调度器实例
monitoring_scheduler = MonitoringScheduler()
