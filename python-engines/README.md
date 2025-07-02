# Python 引擎模块

本目录包含 LingoSub 项目的 Python Sidecar 引擎实现，提供高性能的语音识别和字幕处理能力。

## 模块结构

### 核心引擎
- `funasr_engine/` - FunASR 中文优化语音识别引擎
- `whisper_engine/` - faster-whisper 多语言语音识别引擎
- `netflix_processor/` - Netflix 标准字幕规范化处理器

### 共享组件
- `common/` - 公共模块和工具库
  - 基础 Sidecar 架构
  - 进程间通信接口
  - 数据模型定义
  - 工具函数库

## 技术特性

### 双引擎并行
- FunASR：专注中文识别优化
- faster-whisper：支持多语言高速转录
- 结果对比和质量评估

### Sidecar 架构
- 独立进程隔离
- JSON-RPC 通信协议
- 异步任务处理
- 故障自动恢复

### Netflix 规范化
- 智能断句和拆行
- 字符数和时长控制
- 多语言规范支持
- 质量评分系统

## 开发规范

- 每个模块独立部署
- 统一的错误处理
- 完整的日志记录
- 单元测试覆盖
- 性能基准测试 