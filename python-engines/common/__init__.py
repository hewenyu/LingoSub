"""
Python Sidecar Engine Common Package
公共模块包，包含基础架构和共享组件
"""

from .base_engine import BaseSidecarEngine
from .communication import SidecarCommunicator, JsonRpcProtocol
from .config import SidecarConfig, load_config
from .logger import SidecarLogger, setup_logging
from .lifecycle import ProcessManager, ProcessState
from .models import (
    TranscriptionRequest,
    TranscriptionResponse,
    EngineConfig,
    HealthStatus,
    EngineMetrics,
    TaskStatus,
    EngineType
)
from .test_engine import TestEngine

__version__ = "1.0.0"
__all__ = [
    "BaseSidecarEngine",
    "SidecarCommunicator", 
    "JsonRpcProtocol",
    "SidecarConfig",
    "load_config",
    "SidecarLogger",
    "setup_logging",
    "ProcessManager",
    "ProcessState",
    "TranscriptionRequest",
    "TranscriptionResponse",
    "EngineConfig",
    "HealthStatus",
    "EngineMetrics",
    "TaskStatus",
    "EngineType",
    "TestEngine"
] 