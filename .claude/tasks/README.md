# LingoSub 任务跟踪系统

## 项目概览

LingoSub 是基于 Tauri + 多 Python Sidecar 架构的桌面端字幕工具，实现 Netflix 级别的专业字幕生成。

### 技术架构
- 前端：Tauri + React/TypeScript
- 后端：Rust 协调层 + Python Sidecar 进程
- ASR 引擎：FunASR + faster-whisper 双引擎并行
- 目标：Netflix 标准字幕输出

### 核心特性
- 双引擎并行转录和结果对比
- Netflix 规范化自动处理
- 实时字幕编辑器
- 批量处理和任务队列
- 智能引擎推荐

## 任务分解结构

### 第一阶段：基础架构建设
- [01-project-setup.md](./01-project-setup.md) - 项目初始化和环境配置
- [02-python-engines.md](./02-python-engines.md) - Python ASR 引擎 Sidecar 开发

### 第二阶段：核心功能开发  
- [03-rust-backend.md](./03-rust-backend.md) - Rust 后端协调层开发
- [04-frontend-ui.md](./04-frontend-ui.md) - Tauri 前端界面开发
- [05-netflix-processor.md](./05-netflix-processor.md) - Netflix 规范化处理器

### 第三阶段：集成和优化
- [06-integration.md](./06-integration.md) - 系统集成和测试
- [07-deployment.md](./07-deployment.md) - 打包部署和分发

## 任务执行规则

### 依赖关系
1. 严格按阶段顺序执行
2. 同阶段内任务可并行开发
3. 所有前置任务必须完成验收才能开始后续任务
4. 每个任务完成后需更新状态和输出文档

### 状态标记
- `待开始` - 前置依赖未完成
- `进行中` - 正在开发实现
- `待验收` - 开发完成，等待测试验收
- `已完成` - 验收通过，可作为后续任务依赖

### 文档约定
- 每个任务文件包含完整的实现细节
- 输入输出明确定义
- 实现要点详细说明
- 验收标准可测试
- 所有路径和命名规范统一

## 项目目录结构

```
LingoSub/
├── .claude/tasks/           # 任务跟踪文档
├── src-tauri/              # Rust 后端代码
├── src/                    # 前端代码
├── python-engines/         # Python Sidecar 引擎
├── docs/                   # 项目文档
├── tests/                  # 测试文件
└── scripts/                # 构建和部署脚本
```

## 开发约定

### 代码规范
- Rust 代码遵循 Clippy 标准
- TypeScript 使用严格模式
- Python 遵循 PEP 8 规范
- 每个文件不超过 300 行

### 命名规范
- 文件名使用 kebab-case
- 函数名使用 snake_case (Rust/Python) 或 camelCase (TypeScript)
- 常量使用 SCREAMING_SNAKE_CASE
- 组件名使用 PascalCase

### 测试要求
- 每个模块必须有单元测试
- 集成测试覆盖主要工作流
- 测试覆盖率不低于 80%
- 性能基准测试包含在验收标准中 