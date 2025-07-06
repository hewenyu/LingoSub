"""
Python Sidecar Engine Base Class
基础引擎抽象类，定义所有 ASR 引擎的标准接口
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime
import json

from .models import (
    TranscriptionRequest,
    TranscriptionResponse,
    HealthStatus,
    EngineConfig,
    EngineMetrics
)


class BaseSidecarEngine(ABC):
    """
    Sidecar 引擎基类
    所有 ASR 引擎都应该继承此类并实现抽象方法
    """
    
    def __init__(self, config: EngineConfig):
        """
        初始化引擎
        
        Args:
            config: 引擎配置对象
        """
        self.config = config
        self.engine_id = config.engine_id
        self.logger = logging.getLogger(f"engine.{self.engine_id}")
        self.status = "initializing"
        self.metrics = EngineMetrics(engine_id=self.engine_id)
        self.created_at = datetime.now()
        self.last_heartbeat = datetime.now()
        
        # 初始化引擎特定配置
        self._initialize_engine()
    
    @abstractmethod
    def _initialize_engine(self) -> None:
        """
        引擎特定的初始化逻辑
        子类必须实现此方法
        """
        pass
    
    @abstractmethod
    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
        """
        执行语音转录
        
        Args:
            request: 转录请求对象
            
        Returns:
            TranscriptionResponse: 转录结果
        """
        pass
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理通用请求
        
        Args:
            request_data: 请求数据字典
            
        Returns:
            Dict[str, Any]: 响应数据字典
        """
        try:
            # 更新心跳时间
            self.last_heartbeat = datetime.now()
            
            # 解析请求类型
            request_type = request_data.get("type")
            
            if request_type == "transcribe":
                # 转录请求
                request = TranscriptionRequest(**request_data["payload"])
                response = await self.transcribe(request)
                return {
                    "status": "success",
                    "data": response.model_dump(),
                    "metrics": self.metrics.model_dump()
                }
            
            elif request_type == "health_check":
                # 健康检查
                health = await self.health_check()
                return {
                    "status": "success",
                    "data": health.model_dump()
                }
            
            elif request_type == "get_metrics":
                # 获取指标
                return {
                    "status": "success",
                    "data": self.metrics.model_dump()
                }
            
            else:
                raise ValueError(f"Unknown request type: {request_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}")
            self.metrics.increment_error()
            return {
                "status": "error",
                "error": str(e),
                "type": type(e).__name__
            }
    
    async def health_check(self) -> HealthStatus:
        """
        执行健康检查
        
        Returns:
            HealthStatus: 健康状态对象
        """
        try:
            # 检查引擎状态
            engine_healthy = await self._check_engine_health()
            
            # 计算运行时间
            uptime = (datetime.now() - self.created_at).total_seconds()
            
            # 检查心跳
            last_heartbeat_seconds = (datetime.now() - self.last_heartbeat).total_seconds()
            heartbeat_healthy = last_heartbeat_seconds < 30  # 30秒内有心跳
            
            status = "healthy" if engine_healthy and heartbeat_healthy else "unhealthy"
            
            return HealthStatus(
                status=status,
                engine_id=self.engine_id,
                uptime=uptime,
                last_heartbeat=self.last_heartbeat,
                metrics=self.metrics,
                details={
                    "engine_healthy": engine_healthy,
                    "heartbeat_healthy": heartbeat_healthy,
                    "last_heartbeat_seconds": last_heartbeat_seconds
                }
            )
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return HealthStatus(
                status="error",
                engine_id=self.engine_id,
                uptime=0,
                last_heartbeat=self.last_heartbeat,
                metrics=self.metrics,
                details={"error": str(e)}
            )
    
    @abstractmethod
    async def _check_engine_health(self) -> bool:
        """
        引擎特定的健康检查
        子类必须实现此方法
        
        Returns:
            bool: 引擎是否健康
        """
        pass
    
    async def start(self) -> None:
        """
        启动引擎
        """
        try:
            self.logger.info(f"Starting engine {self.engine_id}")
            await self._start_engine()
            self.status = "running"
            self.logger.info(f"Engine {self.engine_id} started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start engine {self.engine_id}: {str(e)}")
            self.status = "failed"
            raise
    
    async def stop(self) -> None:
        """
        停止引擎
        """
        try:
            self.logger.info(f"Stopping engine {self.engine_id}")
            await self._stop_engine()
            self.status = "stopped"
            self.logger.info(f"Engine {self.engine_id} stopped successfully")
        except Exception as e:
            self.logger.error(f"Failed to stop engine {self.engine_id}: {str(e)}")
            raise
    
    @abstractmethod
    async def _start_engine(self) -> None:
        """
        引擎特定的启动逻辑
        子类必须实现此方法
        """
        pass
    
    @abstractmethod
    async def _stop_engine(self) -> None:
        """
        引擎特定的停止逻辑
        子类必须实现此方法
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取引擎信息
        
        Returns:
            Dict[str, Any]: 引擎信息
        """
        return {
            "engine_id": self.engine_id,
            "engine_type": self.__class__.__name__,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "config": self.config.model_dump()
        } 