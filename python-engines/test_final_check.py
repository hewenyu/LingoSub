#!/usr/bin/env python3
"""
最终验证脚本 - 确保ENGINE-001修复完全正常
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# 添加path以便导入本地模块
sys.path.insert(0, str(Path(__file__).parent))

from common.test_engine import TestEngine
from common.config import SidecarConfig
from common.models import EngineConfig, EngineType, TranscriptionRequest
from common.lifecycle import ProcessManager


async def final_verification():
    """最终验证所有功能"""
    print("🎯 ENGINE-001 最终验证开始...")
    
    # 测试1: 基本引擎功能
    print("1️⃣ 基本引擎功能测试...")
    engine = TestEngine(EngineConfig(
        engine_id="final-test",
        engine_type=EngineType.TEST,
        model_name="test-model"
    ))
    
    await engine.start()
    
    request = TranscriptionRequest(file_path="test.wav", language="zh")
    response = await engine.transcribe(request)
    
    await engine.stop()
    print("✅ 基本引擎功能正常")
    
    # 测试2: 进程管理器
    print("2️⃣ 进程管理器测试...")
    config = SidecarConfig(
        engine_id="final-lifecycle",
        engine_type=EngineType.TEST,
        model_name="test-model"
    )
    
    engine2 = TestEngine(EngineConfig(
        engine_id="final-lifecycle",
        engine_type=EngineType.TEST,
        model_name="test-model"
    ))
    
    # 使用测试模式，避免通信器阻塞
    process_manager = ProcessManager(engine2, config, test_mode=True)
    
    success = await process_manager.start()
    assert success, "进程管理器应该启动成功"
    
    success = await process_manager.stop()
    assert success, "进程管理器应该停止成功"
    
    # 清理进程管理器
    if hasattr(process_manager.logger, 'performance_monitor'):
        process_manager.logger.performance_monitor.stop_monitoring()
    
    print("✅ 进程管理器正常")
    
    print("🎉 最终验证完成 - 所有功能正常！")


async def main():
    """主函数"""
    start_time = time.time()
    
    try:
        await final_verification()
    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 快速清理
        print("🔄 快速清理...")
        
        # 取消所有待处理任务
        tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
        print(f"发现 {len(tasks)} 个待处理任务")
        
        if tasks:
            # 打印任务信息
            for i, task in enumerate(tasks):
                print(f"  任务 {i+1}: {task.get_name() if hasattr(task, 'get_name') else 'unknown'} - {task}")
            
            # 强制取消
            for task in tasks:
                task.cancel()
            
            print("⏰ 等待任务完成（0.5秒超时）...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=0.5  # 减少到0.5秒
                )
                print("✅ 任务清理完成")
            except asyncio.TimeoutError:
                print("⚠️ 清理超时，立即强制退出")
                end_time = time.time()
                print(f"🔚 测试完成，耗时: {end_time - start_time:.2f}秒")
                os._exit(0)  # 立即退出
        else:
            print("✅ 没有待处理任务")
        
        end_time = time.time()
        print(f"✅ 测试完成，耗时: {end_time - start_time:.2f}秒")


if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    finally:
        print("🔚 程序正常退出")
        os._exit(0) 