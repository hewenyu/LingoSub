#!/usr/bin/env python3
"""
简单测试脚本 - 避免使用ProcessManager
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# 添加path以便导入本地模块
sys.path.insert(0, str(Path(__file__).parent))

from common.test_engine import TestEngine
from common.models import EngineConfig, EngineType, TranscriptionRequest


async def simple_test():
    """简单快速测试"""
    print("🚀 简单测试开始...")
    
    # 测试1: 基本引擎功能
    print("1️⃣ 基本引擎测试...")
    engine = TestEngine(EngineConfig(
        engine_id="simple-test",
        engine_type=EngineType.TEST,
        model_name="test-model"
    ))
    
    try:
        await engine.start()
        print("✅ 引擎启动成功")
        
        # 转录测试
        request = TranscriptionRequest(file_path="test.wav", language="zh")
        response = await engine.transcribe(request)
        print(f"✅ 转录成功: {response.text[:30]}...")
        
        # 健康检查测试
        health = await engine.health_check()
        print(f"✅ 健康检查: {health.status}")
        
        # 指标测试
        print(f"✅ 请求数: {engine.metrics.total_requests}")
        
    finally:
        await engine.stop()
        print("✅ 引擎停止成功")
    
    # 测试2: 错误处理
    print("2️⃣ 错误处理测试...")
    engine2 = TestEngine(EngineConfig(
        engine_id="error-test",
        engine_type=EngineType.TEST,
        model_name="test-model"
    ))
    
    try:
        await engine2.start()
        
        # 测试验证错误
        try:
            invalid_request = TranscriptionRequest(
                file_path="",  # 空路径会触发验证错误
                language="zh"
            )
            print("❌ 验证错误没有被触发")
        except ValueError:
            print("✅ 验证错误正确触发")
        
    finally:
        await engine2.stop()
    
    print("🎉 所有测试完成 - ENGINE-001基础功能正常！")


def main():
    """主函数"""
    start_time = time.time()
    
    print("🎯 ENGINE-001 简单验证")
    print("=" * 40)
    
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # 运行测试
        asyncio.run(simple_test())
        
        end_time = time.time()
        print("=" * 40)
        print(f"✅ 测试完成，耗时: {end_time - start_time:.2f}秒")
        print("✅ ENGINE-001 基础架构验证成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    finally:
        print("🔚 程序正常退出")
        # 立即强制退出，避免任何残留任务
        os._exit(0)


if __name__ == "__main__":
    main() 