"""
Tests for BaseSidecarEngine
BaseSidecarEngine 基类的单元测试
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../python-engines'))

from common.base_engine import BaseSidecarEngine
from common.models import (
    EngineConfig, 
    TranscriptionRequest, 
    TranscriptionResponse,
    HealthStatus,
    EngineType,
    TaskStatus
)


class MockEngine(BaseSidecarEngine):
    """测试用的模拟引擎"""
    
    def _initialize_engine(self) -> None:
        self.initialized = True
        
    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
        # 模拟转录实现
        return TranscriptionResponse(
            task_id=request.task_id,
            status=TaskStatus.COMPLETED,
            text="Mock transcription result",
            confidence=0.95,
            processing_time=0.1
        )
    
    async def _check_engine_health(self) -> bool:
        return True
    
    async def _start_engine(self) -> None:
        pass
    
    async def _stop_engine(self) -> None:
        pass


class TestBaseSidecarEngine:
    """BaseSidecarEngine 测试类"""
    
    @pytest.fixture
    def engine_config(self):
        """创建测试用引擎配置"""
        return EngineConfig(
            engine_id="test-engine",
            engine_type=EngineType.TEST,
            model_name="test-model",
            device="cpu",
            language="zh",
            max_workers=1,
            timeout=300
        )
    
    @pytest.fixture
    def mock_engine(self, engine_config):
        """创建模拟引擎实例"""
        return MockEngine(engine_config)
    
    def test_engine_initialization(self, mock_engine):
        """测试引擎初始化"""
        assert mock_engine.engine_id == "test-engine"
        assert mock_engine.status == "initializing"
        assert mock_engine.initialized == True
        assert mock_engine.metrics is not None
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self, mock_engine):
        """测试引擎启动和停止"""
        # 测试启动
        await mock_engine.start()
        assert mock_engine.status == "running"
        
        # 测试停止
        await mock_engine.stop()
        assert mock_engine.status == "stopped"
    
    @pytest.mark.asyncio
    async def test_transcribe_functionality(self, mock_engine):
        """测试转录功能"""
        await mock_engine.start()
        
        request = TranscriptionRequest(
            file_path="/test/audio.wav",
            language="zh"
        )
        
        response = await mock_engine.transcribe(request)
        
        assert response.task_id == request.task_id
        assert response.status == TaskStatus.COMPLETED
        assert response.text == "Mock transcription result"
        assert response.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_engine):
        """测试健康检查"""
        await mock_engine.start()
        
        health = await mock_engine.health_check()
        
        assert isinstance(health, HealthStatus)
        assert health.status == "healthy"
        assert health.engine_id == "test-engine"
        assert health.uptime >= 0
    
    @pytest.mark.asyncio
    async def test_process_request_transcribe(self, mock_engine):
        """测试处理转录请求"""
        await mock_engine.start()
        
        request_data = {
            "type": "transcribe",
            "payload": {
                "task_id": "test-task",
                "file_path": "/test/audio.wav",
                "language": "zh"
            }
        }
        
        response = await mock_engine.process_request(request_data)
        
        assert response["status"] == "success"
        assert "data" in response
        assert response["data"]["status"] == TaskStatus.COMPLETED.value
    
    @pytest.mark.asyncio
    async def test_process_request_health_check(self, mock_engine):
        """测试处理健康检查请求"""
        await mock_engine.start()
        
        request_data = {
            "type": "health_check"
        }
        
        response = await mock_engine.process_request(request_data)
        
        assert response["status"] == "success"
        assert "data" in response
        assert response["data"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_process_request_get_metrics(self, mock_engine):
        """测试获取指标请求"""
        await mock_engine.start()
        
        request_data = {
            "type": "get_metrics"
        }
        
        response = await mock_engine.process_request(request_data)
        
        assert response["status"] == "success"
        assert "data" in response
        assert "engine_id" in response["data"]
    
    @pytest.mark.asyncio
    async def test_process_request_unknown_type(self, mock_engine):
        """测试未知请求类型"""
        await mock_engine.start()
        
        request_data = {
            "type": "unknown_command"
        }
        
        response = await mock_engine.process_request(request_data)
        
        assert response["status"] == "error"
        assert "error" in response
        assert "Unknown request type" in response["error"]
    
    def test_get_info(self, mock_engine):
        """测试获取引擎信息"""
        info = mock_engine.get_info()
        
        assert info["engine_id"] == "test-engine"
        assert info["engine_type"] == "MockEngine"
        assert info["status"] == "initializing"
        assert "created_at" in info
        assert "config" in info
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, mock_engine):
        """测试指标跟踪"""
        await mock_engine.start()
        
        # 初始指标
        initial_requests = mock_engine.metrics.total_requests
        
        # 执行转录请求
        request = TranscriptionRequest(
            file_path="/test/audio.wav",
            language="zh"
        )
        
        await mock_engine.transcribe(request)
        
        # 检查指标更新
        assert mock_engine.metrics.total_requests == initial_requests + 1
        assert mock_engine.metrics.successful_requests == 1
        assert mock_engine.metrics.avg_processing_time > 0


class TestEngineConfigValidation:
    """EngineConfig 验证测试"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config = EngineConfig(
            engine_id="test",
            engine_type=EngineType.TEST,
            model_name="test-model",
            device="cpu"
        )
        
        assert config.engine_id == "test"
        assert config.device == "cpu"
    
    def test_invalid_device(self):
        """测试无效设备配置"""
        with pytest.raises(ValueError, match="Device must be one of"):
            EngineConfig(
                engine_id="test",
                engine_type=EngineType.TEST,
                model_name="test-model",
                device="invalid"
            )


class TestAsyncEngineOperations:
    """异步引擎操作测试"""
    
    @pytest.fixture
    def engine_config(self):
        return EngineConfig(
            engine_id="async-test",
            engine_type=EngineType.TEST,
            model_name="async-model"
        )
    
    @pytest.mark.asyncio
    async def test_concurrent_transcriptions(self, engine_config):
        """测试并发转录"""
        engine = MockEngine(engine_config)
        await engine.start()
        
        # 创建多个请求
        requests = [
            TranscriptionRequest(file_path=f"/test/audio_{i}.wav")
            for i in range(5)
        ]
        
        # 并发执行
        responses = await asyncio.gather(*[
            engine.transcribe(req) for req in requests
        ])
        
        # 验证结果
        assert len(responses) == 5
        for response in responses:
            assert response.status == TaskStatus.COMPLETED
        
        # 验证指标
        assert engine.metrics.total_requests == 5
        assert engine.metrics.successful_requests == 5
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_engine_restart(self, engine_config):
        """测试引擎重启"""
        engine = MockEngine(engine_config)
        
        # 启动
        await engine.start()
        assert engine.status == "running"
        
        # 停止
        await engine.stop()
        assert engine.status == "stopped"
        
        # 重新启动
        await engine.start()
        assert engine.status == "running"
        
        await engine.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 