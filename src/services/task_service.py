"""
异步任务服务
处理长时间运行的后台任务，如 GitLab 数据同步
"""
import uuid
import threading
import time
from datetime import datetime
from typing import Dict, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict, is_dataclass
from utils.logger import get_logger

logger = get_logger(__name__, 'app')


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: int = 0  # 0-100
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        # 处理 result 字段 - 如果是 dataclass，转换为字典
        result_value = self.result
        if result_value is not None and is_dataclass(result_value):
            try:
                result_value = asdict(result_value)
            except Exception as e:
                logger.warning(f"Failed to convert result to dict: {e}")
                result_value = str(result_value)
        
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': result_value,
            'error': self.error,
            'progress': self.progress,
            'message': self.message,
            'metadata': self.metadata,
            'duration': self._get_duration()
        }
    
    def _get_duration(self) -> Optional[float]:
        """计算任务执行时长（秒）"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()


class TaskService:
    """
    任务服务 - 管理异步后台任务
    
    这是一个单例服务，使用内存存储任务状态
    适合中小规模应用，如需持久化可改用 Redis 或数据库
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化任务服务"""
        if self._initialized:
            return
        
        self._initialized = True
        self.tasks: Dict[str, Task] = {}  # 存储所有任务
        self._lock = threading.Lock()
        
        # 防重复机制
        self.running_task_types: set = set()  # 正在运行的任务类型
        self.last_task_time: Dict[str, datetime] = {}  # 最后执行时间
        self.task_type_lock = threading.Lock()
        
        # 启动清理线程（定期清理旧任务）
        self._start_cleanup_thread()
        
        logger.info("任务服务已初始化")
    
    def create_task(
        self,
        task_type: str,
        func: Callable,
        *args,
        allow_duplicate: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建并启动异步任务（带防重复检查）
        
        Args:
            task_type: 任务类型（如 'sync_repositories'）
            func: 要执行的函数
            *args: 函数参数
            allow_duplicate: 是否允许重复任务（默认 False）
            metadata: 任务元数据
            **kwargs: 函数关键字参数
        
        Returns:
            Dict: {
                'task_id': str,
                'is_new': bool,
                'message': str
            }
        """
        
        # 防重复检查
        if not allow_duplicate:
            # 1. 检查是否有相同任务正在运行
            with self.task_type_lock:
                if task_type in self.running_task_types:
                    running_task = self._find_running_task(task_type)
                    
                    if running_task:
                        logger.warning(
                            f"任务类型 {task_type} 已在运行中 "
                            f"(任务ID: {running_task['task_id']})"
                        )
                        
                        return {
                            'task_id': running_task['task_id'],
                            'is_new': False,
                            'message': '已有相同任务正在运行，已返回现有任务'
                        }
                
                # 2. 检查时间窗口（防止频繁执行）
                from config.settings import settings
                min_interval = settings.task.min_interval
                
                last_time = self.last_task_time.get(task_type)
                if last_time:
                    elapsed = (datetime.now() - last_time).total_seconds()
                    
                    if elapsed < min_interval:
                        remaining = int(min_interval - elapsed)
                        error_msg = f"请勿频繁同步，请 {remaining} 秒后再试"
                        
                        logger.warning(
                            f"任务 {task_type} 触发过于频繁 "
                            f"(距上次 {int(elapsed)} 秒，需间隔 {min_interval} 秒)"
                        )
                        
                        raise ValueError(error_msg)
                
                # 标记任务类型为运行中
                self.running_task_types.add(task_type)
                self.last_task_time[task_type] = datetime.now()
        
        # 创建新任务
        task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self.tasks[task_id] = task
        
        logger.info(f"创建任务: {task_type} (ID: {task_id})")
        
        # 在新线程中执行任务
        thread = threading.Thread(
            target=self._execute_task,
            args=(task_id, func, args, kwargs),
            daemon=True
        )
        thread.start()
        
        return {
            'task_id': task_id,
            'is_new': True,
            'message': '任务已创建'
        }
    
    def _execute_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple,
        kwargs: dict
    ):
        """
        执行任务（在独立线程中运行）
        
        Args:
            task_id: 任务 ID
            func: 要执行的函数
            args: 函数参数
            kwargs: 函数关键字参数
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        try:
            # 更新状态为运行中
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.message = "任务执行中..."
            
            logger.info(f"开始执行任务: {task.task_type} (ID: {task_id})")
            
            # 执行实际任务
            result = func(*args, **kwargs)
            
            # 更新状态为完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 100
            task.result = result
            task.message = "任务完成"
            
            logger.info(
                f"任务完成: {task.task_type} (ID: {task_id}) "
                f"- 耗时: {task._get_duration():.2f}秒"
            )
            
        except Exception as e:
            # 更新状态为失败
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            
            # 提取错误信息（保持完整性）
            error_message = str(e)
            
            # 特殊处理 GitLab 认证错误，提取关键信息
            if "GitLab 认证失败" in error_message or "401 Unauthorized" in error_message:
                # 清理和格式化错误消息
                task.error = "GitLab 认证失败 (401 Unauthorized)"
                task.message = (
                    "❌ GitLab 认证失败\n\n"
                    "📋 可能的原因:\n"
                    "  1. Token 已过期或被撤销\n"
                    "  2. Token 权限不足（需要 'api' 或 'read_api' 权限）\n"
                    "  3. GitLab 服务器地址配置错误\n\n"
                    "✅ 解决方案:\n"
                    "  1. 访问 GitLab → Settings → Access Tokens\n"
                    "  2. 创建新 Token（勾选 'api' 权限）\n"
                    "  3. 复制 Token 并更新到 .env 文件的 GITLAB_TOKEN\n"
                    "  4. 重启应用\n\n"
                    "📖 详细指南: docs/GITLAB_TOKEN_GUIDE.md"
                )
                # GitLab 认证错误是已知错误，不需要完整堆栈跟踪
                logger.error(f"任务失败: {task.task_type} (ID: {task_id}) - {error_message}")
            else:
                # 其他未知错误，保持原样并记录完整堆栈跟踪以便调试
                task.error = error_message
                task.message = f"任务执行失败: {error_message}"
                logger.error(
                    f"任务失败: {task.task_type} (ID: {task_id}) - {error_message}",
                    exc_info=True
                )
        
        finally:
            # 任务完成后，移除类型锁
            with self.task_type_lock:
                if task.task_type in self.running_task_types:
                    self.running_task_types.remove(task.task_type)
                    logger.debug(f"已释放任务类型锁: {task.task_type}")
    
    def _find_running_task(self, task_type: str) -> Optional[Dict[str, Any]]:
        """
        查找正在运行的指定类型任务
        
        Args:
            task_type: 任务类型
        
        Returns:
            正在运行的任务信息，如果没有则返回 None
        """
        with self._lock:
            for task in self.tasks.values():
                if (task.task_type == task_type and 
                    task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]):
                    return task.to_dict()
        return None
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务 ID
        
        Returns:
            任务信息字典，如果不存在则返回 None
        """
        task = self.tasks.get(task_id)
        if task:
            return task.to_dict()
        return None
    
    def get_all_tasks(
        self,
        task_type: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> list:
        """
        获取任务列表
        
        Args:
            task_type: 过滤任务类型
            status: 过滤任务状态
            limit: 返回数量限制
        
        Returns:
            任务列表
        """
        with self._lock:
            tasks = list(self.tasks.values())
        
        # 过滤
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 按创建时间倒序排序
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # 限制数量
        tasks = tasks[:limit]
        
        return [task.to_dict() for task in tasks]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务（注意：只能取消等待中的任务）
        
        Args:
            task_id: 任务 ID
        
        Returns:
            bool: 是否成功取消
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            task.message = "任务已取消"
            logger.info(f"任务已取消: {task_id}")
            return True
        
        logger.warning(f"无法取消任务（状态: {task.status}）: {task_id}")
        return False
    
    def update_progress(
        self,
        task_id: str,
        progress: int,
        message: str = ""
    ):
        """
        更新任务进度
        
        Args:
            task_id: 任务 ID
            progress: 进度 (0-100)
            message: 进度消息
        """
        task = self.tasks.get(task_id)
        if task:
            task.progress = max(0, min(100, progress))  # 限制在 0-100
            if message:
                task.message = message
            
            logger.debug(f"任务进度更新: {task_id} - {progress}% - {message}")
    
    def _start_cleanup_thread(self):
        """启动清理线程，定期删除旧任务"""
        def cleanup():
            while True:
                time.sleep(3600)  # 每小时清理一次
                self._cleanup_old_tasks()
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
        logger.info("任务清理线程已启动")
    
    def _cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        清理旧任务
        
        Args:
            max_age_hours: 任务最大保留时长（小时）
        """
        now = datetime.now()
        to_delete = []
        
        with self._lock:
            for task_id, task in self.tasks.items():
                # 只清理已完成/失败/取消的任务
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    age_hours = (now - task.created_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_delete.append(task_id)
            
            for task_id in to_delete:
                del self.tasks[task_id]
        
        if to_delete:
            logger.info(f"清理了 {len(to_delete)} 个旧任务")


# 创建全局任务服务实例
task_service = TaskService()
