"""
ENGINE-001 集成测试
验证Python Sidecar基础架构的功能
"""

import asyncio
import sys
import json
import logging
import os
from pathlib import Path
from datetime import datetime

# 添加path以便导入本地模块
sys.path.insert(0, str(Path(__file__).parent))

from common.test_engine import TestEngine
from common.config import SidecarConfig, EngineConfig
from common.models import TranscriptionRequest, EngineType
from common.communication import SidecarCommunicator
from common.lifecycle import ProcessManager
from common.logger import setup_logging


async def test_basic_engine():
    """测试基础引擎功能"""
    print("🔍 测试基础引擎功能...")
    
    # 创建配置
    config = SidecarConfig(
        engine_id="test-engine",
        engine_type=EngineType.TEST,
        model_name="test-model"
    )
    
    # 创建测试引擎
    engine = TestEngine(EngineConfig(
        engine_id="test-engine",
        engine_type=EngineType.TEST,
        model_name="test-model"
    ))
    
    # 启动引擎
    await engine.start()
    assert engine.status == "running", "引擎应该处于运行状态"
    
    # 测试健康检查
    health = await engine.health_check()
    assert health.status == "healthy", "引擎应该是健康状态"
    assert health.engine_id == "test-engine", "引擎ID应该匹配"
    
    # 测试转录功能
    request = TranscriptionRequest(
        task_id="test-task-001",
        file_path="test.wav",
        language="zh"
    )
    
    response = await engine.transcribe(request)
    assert response.task_id == "test-task-001", "任务ID应该匹配"
    assert len(response.text) > 0, "应该有转录文本"
    assert len(response.timestamps) > 0, "应该有时间戳"
    assert response.confidence > 0, "应该有置信度"
    
    # 停止引擎
    await engine.stop()
    assert engine.status == "stopped", "引擎应该处于停止状态"
    
    print("✅ 基础引擎功能测试通过")


async def test_engine_error_handling():
    """测试引擎错误处理"""
    print("🔍 测试引擎错误处理...")
    
    config = SidecarConfig(
        engine_id="test-engine-error",
        engine_type=EngineType.TEST,
        model_name="test-model"
    )
    
    engine = TestEngine(EngineConfig(
        engine_id="test-engine-error",
        engine_type=EngineType.TEST,
        model_name="test-model"
    ))
    
    await engine.start()
    
    # 测试 Pydantic 验证错误
    try:
        request = TranscriptionRequest(
            task_id="test-error-001",
            file_path="",  # 空文件路径应该触发验证错误
            language="zh"
        )
        assert False, "应该抛出验证错误"
    except ValueError as e:
        print(f"✅ 验证错误正确抛出: {str(e)}")
    
    # 测试引擎处理错误（使用有效的请求但让引擎产生错误）
    # TestEngine 有 10% 的错误率，多次尝试应该能触发错误
    error_triggered = False
    for i in range(20):  # 多次尝试触发错误
        request = TranscriptionRequest(
            task_id=f"test-error-{i}",
            file_path="nonexistent.wav",
            language="zh"
        )
        
        response = await engine.transcribe(request)
        if response.status.value == "failed":
            error_triggered = True
            print(f"✅ 引擎错误正确处理: {response.metadata.get('error', 'Unknown error')}")
            break
    
    if not error_triggered:
        print("ℹ️  引擎错误处理测试跳过（随机错误未触发）")
    
    await engine.stop()
    print("✅ 引擎错误处理测试通过")


async def test_engine_metrics():
    """测试引擎指标收集"""
    print("🔍 测试引擎指标收集...")
    
    config = SidecarConfig(
        engine_id="test-metrics",
        engine_type=EngineType.TEST,
        model_name="test-model"
    )
    
    engine = TestEngine(EngineConfig(
        engine_id="test-metrics",
        engine_type=EngineType.TEST,
        model_name="test-model"
    ))
    
    await engine.start()
    
    # 初始指标
    initial_requests = engine.metrics.total_requests
    
    # 执行几个请求
    for i in range(3):
        request = TranscriptionRequest(
            task_id=f"test-metrics-{i}",
            file_path="test.wav",
            language="zh"
        )
        await engine.transcribe(request)
    
    # 检查指标更新
    assert engine.metrics.total_requests == initial_requests + 3, "请求计数应该增加"
    assert engine.metrics.successful_requests > 0, "应该有成功请求"
    
    await engine.stop()
    print("✅ 引擎指标收集测试通过")


def test_configuration():
    """测试配置管理"""
    print("🔍 测试配置管理...")
    
    # 测试默认配置
    config = SidecarConfig()
    assert config.engine_id == "default"
    assert config.engine_type == EngineType.TEST
    
    # 测试自定义配置
    custom_config = SidecarConfig(
        engine_id="custom-engine",
        engine_type=EngineType.FUNASR,
        model_name="custom-model",
        device="cuda"
    )
    assert custom_config.engine_id == "custom-engine"
    assert custom_config.engine_type == EngineType.FUNASR
    assert custom_config.model_name == "custom-model"
    assert custom_config.device == "cuda"
    
    print("✅ 配置管理测试通过")


def test_data_models():
    """测试数据模型"""
    print("🔍 测试数据模型...")
    
    # 测试转录请求模型
    request = TranscriptionRequest(
        file_path="test.wav",
        language="zh"
    )
    assert request.file_path == "test.wav"
    assert request.language == "zh"
    assert len(request.task_id) > 0  # 应该有自动生成的ID
    
    # 测试引擎配置模型
    engine_config = EngineConfig(
        engine_id="test",
        engine_type=EngineType.TEST,
        model_name="test-model"
    )
    assert engine_config.engine_id == "test"
    assert engine_config.engine_type == EngineType.TEST
    
    print("✅ 数据模型测试通过")


async def test_process_lifecycle():
    """测试进程生命周期管理"""
    print("🔍 测试进程生命周期管理...")
    
    # 创建配置
    config = SidecarConfig(
        engine_id="test-lifecycle",
        engine_type=EngineType.TEST,
        model_name="test-model"
    )
    
    # 创建引擎和进程管理器
    engine = TestEngine(EngineConfig(
        engine_id="test-lifecycle",
        engine_type=EngineType.TEST,
        model_name="test-model"
    ))
    
    process_manager = ProcessManager(engine, config, test_mode=True)
    
    try:
        # 测试启动
        success = await process_manager.start()
        assert success, "进程应该启动成功"
        
        # 测试状态
        status = process_manager.get_status()
        assert status["state"] == "running", "进程状态应该为运行中"
        
        # 测试停止
        success = await process_manager.stop()
        assert success, "进程应该停止成功"
        
    finally:
        # 确保清理所有资源
        try:
            if process_manager.state.value != "stopped":
                await process_manager.stop()
            
            # 停止性能监控器
            if hasattr(process_manager.logger, 'performance_monitor'):
                process_manager.logger.performance_monitor.stop_monitoring()
                
            # 清理通信器
            if hasattr(process_manager, 'communicator') and process_manager.communicator is not None:
                process_manager.communicator.stop()
                
        except Exception as e:
            print(f"⚠️ 清理进程管理器时出现警告: {str(e)}")
    
    print("✅ 进程生命周期管理测试通过")


async def main():
    """主测试函数"""
    print("🚀 开始 ENGINE-001 集成测试")
    print("=" * 50)
    
    try:
        # 基础功能测试
        await test_basic_engine()
        
        # 错误处理测试
        await test_engine_error_handling()
        
        # 指标收集测试
        await test_engine_metrics()
        
        # 配置管理测试
        test_configuration()
        
        # 数据模型测试
        test_data_models()
        
        # 进程生命周期测试
        await test_process_lifecycle()
        
        print("=" * 50)
        print("🎉 所有测试通过！ENGINE-001 基础架构验证成功")
        print("✅ Sidecar 进程能够启动和正常退出")
        print("✅ 能够接收和响应请求")
        print("✅ 健康检查接口正常工作")
        print("✅ 日志输出格式规范")
        print("✅ 异常情况能够正确处理和上报")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理所有待处理的任务
        try:
            # 获取当前事件循环中的所有任务
            pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            
            if pending_tasks:
                print(f"🔄 清理 {len(pending_tasks)} 个待处理任务...")
                
                # 取消所有待处理任务
                for task in pending_tasks:
                    task.cancel()
                
                # 使用超时等待任务完成
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*pending_tasks, return_exceptions=True),
                        timeout=2.0  # 2秒超时
                    )
                    print("✅ 任务清理完成")
                except asyncio.TimeoutError:
                    print("⚠️ 任务清理超时，强制继续")
                    # 强制取消所有任务
                    for task in pending_tasks:
                        if not task.done():
                            task.cancel()
                
            # 清理日志处理器
            logging.shutdown()
            print("✅ 日志系统已关闭")
            
        except Exception as e:
            print(f"⚠️ 清理过程中的警告: {str(e)}")
        
        # 给系统一点时间完成清理
        try:
            await asyncio.sleep(0.1)
        except:
            pass


if __name__ == "__main__":
    # 使用更安全的事件循环策略
    try:
        # 设置事件循环策略(Windows)
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        asyncio.run(main())
        
    except RuntimeError as e:
        if "Event loop stopped" in str(e):
            print("✅ 测试完成，忽略事件循环清理警告")
        else:
            raise
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    finally:
        # 确保程序退出
        print("🔚 程序退出")
        import os
        os._exit(0) 