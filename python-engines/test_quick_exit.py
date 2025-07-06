#!/usr/bin/env python3
"""
快速测试脚本 - 验证程序能否正确退出
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加path以便导入本地模块
sys.path.insert(0, str(Path(__file__).parent))

from common.test_engine import TestEngine
from common.config import SidecarConfig
from common.models import EngineConfig, EngineType, TranscriptionRequest


async def quick_test():
    """快速测试引擎基本功能"""
    print("🚀 快速测试开始...")
    
    # 创建测试引擎
    engine = TestEngine(EngineConfig(
        engine_id="quick-test",
        engine_type=EngineType.TEST,
        model_name="test-model"
    ))
    
    try:
        # 启动引擎
        await engine.start()
        print("✅ 引擎启动成功")
        
        # 测试转录
        request = TranscriptionRequest(
            file_path="test.wav",
            language="zh"
        )
        
        response = await engine.transcribe(request)
        print(f"✅ 转录成功: {response.text[:20]}...")
        
        # 测试健康检查
        health = await engine.health_check()
        print(f"✅ 健康检查: {health.status}")
        
    finally:
        # 停止引擎
        await engine.stop()
        print("✅ 引擎停止成功")
    
    print("🎉 快速测试完成")


async def main():
    """主函数"""
    try:
        await quick_test()
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        sys.exit(1)
    finally:
        # 强制清理
        print("🔄 清理资源...")
        
        # 取消所有待处理任务
        tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        print("✅ 清理完成")


if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    finally:
        print("🔚 程序退出")
        os._exit(0) 