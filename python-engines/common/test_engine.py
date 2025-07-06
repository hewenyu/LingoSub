"""
Test Engine Implementation
测试引擎实现，用于验证 Sidecar 基础架构
"""

import asyncio
import time
import random
from datetime import datetime
from typing import Dict, Any

from .base_engine import BaseSidecarEngine
from .models import (
    TranscriptionRequest, 
    TranscriptionResponse, 
    TimeStamp, 
    EngineConfig,
    TaskStatus,
    EngineType
)
from .config import SidecarConfig


class TestEngine(BaseSidecarEngine):
    """
    测试引擎
    实现简单的回显和模拟转录功能，用于验证架构
    
    Note: 此类不是pytest测试类，是实际的引擎实现
    """
    __test__ = False  # 告诉pytest这不是测试类
    
    def _initialize_engine(self) -> None:
        """初始化测试引擎"""
        self.logger.info("Initializing test engine")
        self.model_loaded = False
        self.processing_delay = 1.0  # 模拟处理延迟
        self.error_rate = 0.1  # 10% 错误率用于测试
        
    async def _start_engine(self) -> None:
        """启动引擎"""
        self.logger.info("Starting test engine")
        
        # 模拟模型加载
        await asyncio.sleep(0.5)
        self.model_loaded = True
        
        self.logger.info("Test engine started successfully")
    
    async def _stop_engine(self) -> None:
        """停止引擎"""
        self.logger.info("Stopping test engine")
        self.model_loaded = False
        self.logger.info("Test engine stopped")
    
    async def _check_engine_health(self) -> bool:
        """检查引擎健康状态"""
        # 简单检查模型是否加载
        return self.model_loaded and self.status == "running"
    
    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
        """
        执行模拟转录
        
        Args:
            request: 转录请求
            
        Returns:
            TranscriptionResponse: 转录结果
        """
        start_time = datetime.now()
        
        try:
            # 更新指标
            self.metrics.increment_request()
            
            self.logger.info(f"Processing transcription request: {request.task_id}")
            
            # 验证输入
            if not request.file_path:
                raise ValueError("File path is required")
            
            # 模拟处理延迟
            processing_delay = self.processing_delay + random.uniform(0, 0.5)
            await asyncio.sleep(processing_delay)
            
            # 模拟错误
            if random.random() < self.error_rate:
                raise RuntimeError("Simulated processing error")
            
            # 生成模拟转录结果
            transcription_result = self._generate_mock_result(request)
            
            # 计算处理时间
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # 更新指标
            self.metrics.increment_success(processing_time)
            
            # 创建响应
            response = TranscriptionResponse(
                task_id=request.task_id,
                status=TaskStatus.COMPLETED,
                text=transcription_result["text"],
                timestamps=transcription_result["timestamps"],
                confidence=transcription_result["confidence"],
                language=request.language or "zh",
                duration=transcription_result["duration"],
                processing_time=processing_time,
                metadata={
                    "engine": "test",
                    "model": self.config.model_name,
                    "processing_delay": processing_delay
                },
                created_at=start_time,
                completed_at=end_time
            )
            
            self.logger.info(
                f"Transcription completed: {request.task_id} in {processing_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            self.metrics.increment_error()
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 创建错误响应
            response = TranscriptionResponse(
                task_id=request.task_id,
                status=TaskStatus.FAILED,
                text="",
                timestamps=[],
                confidence=0.0,
                language=request.language or "zh",
                processing_time=processing_time,
                metadata={
                    "engine": "test",
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                created_at=start_time,
                completed_at=datetime.now()
            )
            
            self.logger.error(f"Transcription failed: {request.task_id} - {str(e)}")
            return response
    
    def _generate_mock_result(self, request: TranscriptionRequest) -> Dict[str, Any]:
        """生成模拟转录结果"""
        
        # 模拟文本内容
        mock_texts = [
            "这是一段测试音频的转录结果",
            "LingoSub 是一个专业的字幕生成工具",
            "我们正在测试语音识别引擎的功能",
            "今天天气很好，适合进行软件开发",
            "人工智能技术正在快速发展"
        ]
        
        # 随机选择文本
        text = random.choice(mock_texts)
        
        # 生成时间戳
        timestamps = self._generate_mock_timestamps(text)
        
        # 模拟音频时长
        duration = timestamps[-1].end if timestamps else 5.0
        
        # 模拟置信度
        confidence = random.uniform(0.7, 0.95)
        
        return {
            "text": text,
            "timestamps": timestamps,
            "duration": duration,
            "confidence": confidence
        }
    
    def _generate_mock_timestamps(self, text: str) -> list[TimeStamp]:
        """生成模拟时间戳"""
        timestamps = []
        words = text.split()
        current_time = 0.0
        
        for i, word in enumerate(words):
            start_time = current_time
            duration = random.uniform(0.3, 0.8)  # 每个词0.3-0.8秒
            end_time = start_time + duration
            
            timestamp = TimeStamp(
                start=start_time,
                end=end_time,
                text=word,
                confidence=random.uniform(0.7, 0.95)
            )
            
            timestamps.append(timestamp)
            current_time = end_time + random.uniform(0.1, 0.3)  # 间隔
        
        return timestamps


def create_test_engine(config: SidecarConfig) -> TestEngine:
    """创建测试引擎实例"""
    
    # 创建引擎配置
    engine_config = EngineConfig(
        engine_id=config.engine_id,
        engine_type=EngineType.TEST,
        model_name=config.model_name,
        device=config.device,
        language=config.language,
        max_workers=config.performance.max_workers,
        timeout=config.performance.timeout,
        options=config.extensions
    )
    
    return TestEngine(engine_config)


# 测试引擎的主函数
async def test_engine_standalone():
    """独立测试引擎功能"""
    from .config import SidecarConfig, PerformanceConfig, LoggingConfig
    
    # 创建测试配置
    config = SidecarConfig(
        engine_id="test-001",
        engine_type=EngineType.TEST,
        model_name="test-model",
        device="cpu",
        language="zh",
        performance=PerformanceConfig(max_workers=1),
        logging=LoggingConfig(level="INFO")
    )
    
    # 创建测试引擎
    engine = create_test_engine(config)
    
    try:
        # 启动引擎
        await engine.start()
        
        # 创建测试请求
        request = TranscriptionRequest(
            file_path="/tmp/test_audio.wav",
            language="zh",
            options={"test": True}
        )
        
        print(f"Testing transcription with request: {request.task_id}")
        
        # 执行转录
        response = await engine.transcribe(request)
        
        print(f"Transcription result:")
        print(f"  Status: {response.status}")
        print(f"  Text: {response.text}")
        print(f"  Confidence: {response.confidence}")
        print(f"  Processing time: {response.processing_time:.3f}s")
        print(f"  Timestamps: {len(response.timestamps)}")
        
        # 测试健康检查
        health = await engine.health_check()
        print(f"Health check: {health.status}")
        
        # 测试指标
        print(f"Engine metrics: {engine.metrics.model_dump()}")
        
    finally:
        # 停止引擎
        await engine.stop()


# 批量测试功能
async def test_engine_batch():
    """批量测试引擎性能"""
    from .config import SidecarConfig, PerformanceConfig, LoggingConfig
    
    config = SidecarConfig(
        engine_id="test-batch",
        engine_type=EngineType.TEST,
        model_name="test-model-batch",
        device="cpu",
        language="zh",
        performance=PerformanceConfig(max_workers=1),
        logging=LoggingConfig(level="WARNING")  # 减少日志输出
    )
    
    engine = create_test_engine(config)
    
    try:
        await engine.start()
        
        # 批量测试
        num_requests = 10
        print(f"Running batch test with {num_requests} requests...")
        
        start_time = time.time()
        tasks = []
        
        for i in range(num_requests):
            request = TranscriptionRequest(
                file_path=f"/tmp/test_audio_{i}.wav",
                language="zh"
            )
            tasks.append(engine.transcribe(request))
        
        # 并发执行
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 统计结果
        successful = 0
        failed = 0
        
        for response in responses:
            if isinstance(response, Exception):
                failed += 1
            elif response.status == TaskStatus.COMPLETED:
                successful += 1
            else:
                failed += 1
        
        print(f"Batch test results:")
        print(f"  Total requests: {num_requests}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Average time per request: {total_time/num_requests:.3f}s")
        print(f"  Requests per second: {num_requests/total_time:.2f}")
        
        # 引擎指标
        metrics = engine.metrics
        print(f"Engine metrics:")
        print(f"  Total requests: {metrics.total_requests}")
        print(f"  Successful requests: {metrics.successful_requests}")
        print(f"  Failed requests: {metrics.failed_requests}")
        print(f"  Average processing time: {metrics.avg_processing_time:.3f}s")
        
    finally:
        await engine.stop()


if __name__ == "__main__":
    print("Testing LingoSub Test Engine")
    print("=" * 50)
    
    print("\n1. Testing standalone functionality...")
    asyncio.run(test_engine_standalone())
    
    print("\n2. Testing batch performance...")
    asyncio.run(test_engine_batch())
    
    print("\nAll tests completed!") 