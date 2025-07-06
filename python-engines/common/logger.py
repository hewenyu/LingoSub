"""
Logging and Monitoring System
日志和监控系统，支持结构化日志和性能监控
"""

import logging
import logging.handlers
import json
import time
import psutil
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps

from .config import LoggingConfig


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricEntry:
    """指标条目"""
    timestamp: datetime
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if self.include_extra:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                             'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                             'thread', 'threadName', 'processName', 'process', 'message', 'exc_info',
                             'exc_text', 'stack_info']:
                    extra_fields[key] = value
            
            if extra_fields:
                log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry, ensure_ascii=False)


class SidecarLogger:
    """Sidecar 日志管理器"""
    
    def __init__(self, config: LoggingConfig, engine_id: str = "default"):
        self.config = config
        self.engine_id = engine_id
        self.logger = logging.getLogger(f"sidecar.{engine_id}")
        self.metrics_logger = logging.getLogger(f"metrics.{engine_id}")
        self.performance_logger = logging.getLogger(f"performance.{engine_id}")
        
        # 设置日志级别
        self.logger.setLevel(getattr(logging, config.level.upper()))
        
        # 配置处理器
        self._setup_handlers()
        
        # 性能监控
        self.performance_monitor = PerformanceMonitor(engine_id)
        
        # 记录启动
        self.logger.info(f"Sidecar logger initialized for engine {engine_id}")
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 控制台处理器
        if self.config.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(console_handler)
        
        # 文件处理器
        if self.config.file_path:
            file_path = Path(self.config.file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                filename=file_path,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)
    
    def log_request(self, request_id: str, method: str, params: Dict[str, Any]):
        """记录请求"""
        self.logger.info(
            f"Request received: {method}",
            extra={
                "request_id": request_id,
                "method": method,
                "params_count": len(params),
                "event_type": "request"
            }
        )
    
    def log_response(self, request_id: str, status: str, processing_time: float):
        """记录响应"""
        level = logging.INFO if status == "success" else logging.ERROR
        self.logger.log(
            level,
            f"Request completed: {status}",
            extra={
                "request_id": request_id,
                "status": status,
                "processing_time": processing_time,
                "event_type": "response"
            }
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """记录错误"""
        self.logger.error(
            f"Error occurred: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "context": context or {},
                "event_type": "error"
            },
            exc_info=True
        )
    
    def log_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """记录指标"""
        self.metrics_logger.info(
            f"Metric: {metric_name} = {value}",
            extra={
                "metric_name": metric_name,
                "metric_value": value,
                "tags": tags or {},
                "event_type": "metric"
            }
        )
    
    def log_performance(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """记录性能指标"""
        self.performance_logger.info(
            f"Performance: {operation} took {duration:.3f}s",
            extra={
                "operation": operation,
                "duration": duration,
                "metadata": metadata or {},
                "event_type": "performance"
            }
        )
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """获取子日志器"""
        if name:
            return logging.getLogger(f"sidecar.{self.engine_id}.{name}")
        return self.logger


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, engine_id: str):
        self.engine_id = engine_id
        self.logger = logging.getLogger(f"performance.{engine_id}")
        self.metrics = {}
        self.start_time = time.time()
        
        # 系统资源监控
        self.process = psutil.Process()
        self.monitoring_thread = None
        self.monitoring_active = False
    
    def start_monitoring(self, interval: float = 5.0):
        """开始监控"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
    
    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self.monitoring_active:
            try:
                # 收集系统指标
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_percent = self.process.memory_percent()
                
                # 记录指标
                self.logger.info(
                    "System metrics",
                    extra={
                        "cpu_percent": cpu_percent,
                        "memory_rss": memory_info.rss,
                        "memory_vms": memory_info.vms,
                        "memory_percent": memory_percent,
                        "uptime": time.time() - self.start_time,
                        "event_type": "system_metrics"
                    }
                )
                
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(interval)
    
    @contextmanager
    def time_operation(self, operation_name: str):
        """操作计时上下文管理器"""
        start_time = time.time()
        start_memory = self.process.memory_info().rss
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self.process.memory_info().rss
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            self.logger.info(
                f"Operation completed: {operation_name}",
                extra={
                    "operation": operation_name,
                    "duration": duration,
                    "memory_delta": memory_delta,
                    "event_type": "operation_timing"
                }
            )
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录自定义指标"""
        self.metrics[name] = {
            "value": value,
            "timestamp": time.time(),
            "tags": tags or {}
        }
        
        self.logger.info(
            f"Custom metric: {name} = {value}",
            extra={
                "metric_name": name,
                "metric_value": value,
                "tags": tags or {},
                "event_type": "custom_metric"
            }
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return {
            "uptime": time.time() - self.start_time,
            "custom_metrics": self.metrics,
            "system_metrics": {
                "cpu_percent": self.process.cpu_percent(),
                "memory_info": self.process.memory_info()._asdict(),
                "memory_percent": self.process.memory_percent(),
            }
        }


def performance_timer(operation_name: str = None):
    """性能计时装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试获取实例的日志器
            logger = None
            if args and hasattr(args[0], 'logger'):
                logger = args[0].logger
            else:
                logger = logging.getLogger("performance")
            
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Function {name} completed in {duration:.3f}s",
                    extra={
                        "function": name,
                        "duration": duration,
                        "status": "success",
                        "event_type": "function_timing"
                    }
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Function {name} failed after {duration:.3f}s: {str(e)}",
                    extra={
                        "function": name,
                        "duration": duration,
                        "status": "error",
                        "error": str(e),
                        "event_type": "function_timing"
                    }
                )
                raise
        
        return wrapper
    return decorator


def setup_logging(config: LoggingConfig, engine_id: str = "default") -> SidecarLogger:
    """设置日志系统"""
    return SidecarLogger(config, engine_id)


def create_logger(name: str, level: str = "INFO") -> logging.Logger:
    """创建简单日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


class LogCollector:
    """日志收集器"""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.log_buffer: List[LogEntry] = []
        self.metric_buffer: List[MetricEntry] = []
        self.lock = threading.Lock()
    
    def collect_log(self, entry: LogEntry):
        """收集日志条目"""
        with self.lock:
            self.log_buffer.append(entry)
            if len(self.log_buffer) > self.buffer_size:
                self.log_buffer.pop(0)
    
    def collect_metric(self, entry: MetricEntry):
        """收集指标条目"""
        with self.lock:
            self.metric_buffer.append(entry)
            if len(self.metric_buffer) > self.buffer_size:
                self.metric_buffer.pop(0)
    
    def get_logs(self, limit: int = None) -> List[LogEntry]:
        """获取日志条目"""
        with self.lock:
            if limit:
                return self.log_buffer[-limit:]
            return self.log_buffer.copy()
    
    def get_metrics(self, limit: int = None) -> List[MetricEntry]:
        """获取指标条目"""
        with self.lock:
            if limit:
                return self.metric_buffer[-limit:]
            return self.metric_buffer.copy()
    
    def clear(self):
        """清空缓冲区"""
        with self.lock:
            self.log_buffer.clear()
            self.metric_buffer.clear() 