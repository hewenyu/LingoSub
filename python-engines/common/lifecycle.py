"""
Process Lifecycle Management
进程生命周期管理，处理启动、停止、重启和健康检查
"""

import asyncio
import signal
import sys
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum
import traceback

from .base_engine import BaseSidecarEngine
from .communication import SidecarCommunicator
from .config import SidecarConfig, load_config
from .logger import SidecarLogger, setup_logging


class ProcessState(str, Enum):
    """进程状态枚举"""
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RESTARTING = "restarting"


class ProcessManager:
    """进程管理器"""
    
    def __init__(self, engine: BaseSidecarEngine, config: SidecarConfig, test_mode: bool = False):
        self.engine = engine
        self.config = config
        self.test_mode = test_mode  # 添加测试模式标志
        self.state = ProcessState.INITIALIZING
        self.start_time = None
        self.stop_time = None
        self.restart_count = 0
        self.max_restarts = 3
        self.restart_delay = 5.0
        
        # 设置日志
        self.logger = setup_logging(config.logging, engine.engine_id)
        
        # 通信器（测试模式下不创建）
        if not test_mode:
            self.communicator = SidecarCommunicator(self._handle_command)
        else:
            self.communicator = None
        
        # 信号处理
        self._setup_signal_handlers()
        
        # 健康检查
        self.health_check_interval = 30.0
        self.health_check_task = None
        
        # 停止事件
        self.stop_event = asyncio.Event()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        if sys.platform != "win32":
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGHUP, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.logger.info(f"Received signal {signum}")
        
        if signum in (signal.SIGINT, signal.SIGTERM):
            # 优雅关闭
            asyncio.create_task(self.stop())
        elif signum == signal.SIGHUP:
            # 重启
            asyncio.create_task(self.restart())
    
    async def start(self) -> bool:
        """启动进程"""
        if self.state in (ProcessState.RUNNING, ProcessState.STARTING):
            self.logger.logger.warning("Process already running or starting")
            return False
        
        try:
            self.logger.logger.info("Starting process...")
            self.state = ProcessState.STARTING
            self.start_time = datetime.now()
            
            # 启动引擎
            await self.engine.start()
            
            # 启动通信器（如果存在）
            if self.communicator:
                asyncio.create_task(self.communicator.start())
            
            # 启动健康检查
            await self._start_health_check()
            
            # 启动性能监控
            self.logger.performance_monitor.start_monitoring()
            
            self.state = ProcessState.RUNNING
            self.logger.logger.info("Process started successfully")
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to start process: {str(e)}")
            self.state = ProcessState.FAILED
            await self._handle_start_failure(e)
            return False
    
    async def stop(self) -> bool:
        """停止进程"""
        if self.state in (ProcessState.STOPPED, ProcessState.STOPPING):
            self.logger.logger.warning("Process already stopped or stopping")
            return False
        
        try:
            self.logger.logger.info("Stopping process...")
            self.state = ProcessState.STOPPING
            
            # 设置停止事件
            self.stop_event.set()
            
            # 停止健康检查
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 停止性能监控
            self.logger.performance_monitor.stop_monitoring()
            
            # 停止通信器
            if self.communicator:
                self.communicator.stop()
            
            # 停止引擎
            await self.engine.stop()
            
            self.state = ProcessState.STOPPED
            self.stop_time = datetime.now()
            self.logger.logger.info("Process stopped successfully")
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Error stopping process: {str(e)}")
            self.state = ProcessState.FAILED
            return False
    
    async def restart(self) -> bool:
        """重启进程"""
        if self.restart_count >= self.max_restarts:
            self.logger.logger.error(f"Maximum restart attempts ({self.max_restarts}) reached")
            return False
        
        self.logger.logger.info(f"Restarting process (attempt {self.restart_count + 1}/{self.max_restarts})")
        self.state = ProcessState.RESTARTING
        self.restart_count += 1
        
        try:
            # 停止进程
            await self.stop()
            
            # 等待重启延迟
            await asyncio.sleep(self.restart_delay)
            
            # 启动进程
            success = await self.start()
            
            if success:
                self.restart_count = 0  # 重置重启计数
                self.logger.logger.info("Process restarted successfully")
                return True
            else:
                self.logger.logger.error("Failed to restart process")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error restarting process: {str(e)}")
            self.state = ProcessState.FAILED
            return False
    
    async def _handle_start_failure(self, error: Exception):
        """处理启动失败"""
        self.logger.log_error(error, {"event": "start_failure"})
        
        # 尝试重启
        if self.restart_count < self.max_restarts:
            self.logger.logger.info("Attempting to restart after start failure")
            await asyncio.sleep(self.restart_delay)
            await self.restart()
        else:
            self.logger.logger.error("Maximum restart attempts reached, giving up")
            self.state = ProcessState.FAILED
    
    async def _start_health_check(self):
        """启动健康检查"""
        self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while not self.stop_event.is_set():
            try:
                # 执行健康检查
                health_status = await self.engine.health_check()
                
                # 记录健康状态
                self.logger.log_metric("health_status", 1 if health_status.status == "healthy" else 0)
                
                # 如果不健康，尝试重启
                if health_status.status != "healthy":
                    self.logger.logger.warning(f"Health check failed: {health_status.status}")
                    await self.restart()
                    break
                
                # 等待下次检查
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.logger.error(f"Error in health check: {str(e)}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _handle_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理命令"""
        try:
            # 处理引擎命令
            if command_data.get("type") in ["transcribe", "health_check", "get_metrics"]:
                return await self.engine.process_request(command_data)
            
            # 处理管理命令
            elif command_data.get("type") == "get_status":
                return await self._get_process_status()
            
            elif command_data.get("type") == "restart":
                success = await self.restart()
                return {"success": success}
            
            elif command_data.get("type") == "stop":
                success = await self.stop()
                return {"success": success}
            
            else:
                raise ValueError(f"Unknown command type: {command_data.get('type')}")
                
        except Exception as e:
            self.logger.log_error(e, {"command": command_data})
            raise
    
    async def _get_process_status(self) -> Dict[str, Any]:
        """获取进程状态"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        health_status = await self.engine.health_check()
        
        return {
            "state": self.state.value,
            "engine_id": self.engine.engine_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "restart_count": self.restart_count,
            "health_status": health_status.model_dump(),
            "uptime": uptime,
            "is_healthy": health_status.status == "healthy"
        }
    
    async def run(self):
        """运行进程主循环"""
        try:
            # 启动进程
            success = await self.start()
            if not success:
                return
            
            # 等待停止信号
            await self.stop_event.wait()
            
        except Exception as e:
            self.logger.logger.error(f"Error in main loop: {str(e)}")
            self.logger.log_error(e, {"event": "main_loop_error"})
        finally:
            # 确保进程正确停止
            await self.stop()
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态（同步版本）"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "state": self.state.value,
            "engine_id": self.engine.engine_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "restart_count": self.restart_count,
            "uptime": uptime,
            # 注意：同步函数中无法调用异步的health_check，状态可能不完整
            "health_status": None,
            "is_healthy": self.state == ProcessState.RUNNING
        }


class ProcessRunner:
    """进程运行器"""
    
    def __init__(self, engine_factory: Callable[[SidecarConfig], BaseSidecarEngine]):
        self.engine_factory = engine_factory
        self.config = None
        self.engine = None
        self.process_manager = None
    
    def initialize(self, config_file: Optional[str] = None) -> bool:
        """初始化"""
        try:
            # 加载配置
            self.config = load_config(config_file)
            
            # 创建引擎
            self.engine = self.engine_factory(self.config)
            
            # 创建进程管理器
            self.process_manager = ProcessManager(self.engine, self.config)
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize: {str(e)}")
            traceback.print_exc()
            return False
    
    async def run_async(self):
        """异步运行"""
        if not self.process_manager:
            raise RuntimeError("Process runner not initialized")
        
        await self.process_manager.run()
    
    def run(self):
        """运行"""
        if not self.initialize():
            sys.exit(1)
        
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            print("Interrupted by user")
        except Exception as e:
            print(f"Error running process: {str(e)}")
            traceback.print_exc()
            sys.exit(1)


def create_process_runner(engine_factory: Callable[[SidecarConfig], BaseSidecarEngine]) -> ProcessRunner:
    """创建进程运行器"""
    return ProcessRunner(engine_factory)


def run_sidecar(engine_factory: Callable[[SidecarConfig], BaseSidecarEngine], config_file: Optional[str] = None):
    """运行 Sidecar 进程的便捷函数"""
    runner = create_process_runner(engine_factory)
    
    # 允许传入配置文件路径
    if config_file:
        runner.config_file = config_file
    
    runner.run()


# 优雅关闭上下文管理器
class GracefulShutdown:
    """优雅关闭管理器"""
    
    def __init__(self, process_manager: ProcessManager):
        self.process_manager = process_manager
        self.original_handlers = {}
    
    def __enter__(self):
        # 保存原有信号处理器
        self.original_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, self._signal_handler)
        self.original_handlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, self._signal_handler)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复原有信号处理器
        for sig, handler in self.original_handlers.items():
            signal.signal(sig, handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"Received signal {signum}, initiating graceful shutdown...")
        
        # 创建异步任务来停止进程
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.process_manager.stop())
        else:
            asyncio.run(self.process_manager.stop())


# 进程监控器
class ProcessMonitor:
    """进程监控器"""
    
    def __init__(self, process_manager: ProcessManager):
        self.process_manager = process_manager
        self.monitoring_thread = None
        self.monitoring_active = False
    
    def start_monitoring(self, interval: float = 10.0):
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
            self.monitoring_thread.join(timeout=5.0)
    
    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self.monitoring_active:
            try:
                status = self.process_manager.get_status()
                
                # 检查进程状态
                if status["state"] == ProcessState.FAILED:
                    print(f"Process failed, attempting restart...")
                    # 在主线程中处理重启
                    asyncio.create_task(self.process_manager.restart())
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in monitoring loop: {str(e)}")
                time.sleep(interval) 