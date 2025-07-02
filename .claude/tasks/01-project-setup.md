# 01 项目初始化和环境配置

## 任务概览

建立完整的开发环境和项目基础架构，为后续开发奠定基础。

## 任务列表

### 1.1 开发环境准备

**任务ID**: SETUP-001  
**状态**: 待开始  
**前置依赖**: 无  

**目的**: 配置完整的开发环境，确保所有工具链正常工作

**输入**: 
- Windows 10/11 开发机器
- 网络连接

**输出**:
- 配置完成的开发环境
- 环境验证报告

**实现要点**:
1. 安装 Rust 工具链 (rustc 1.70+)
2. 安装 Node.js 18+ 和 npm/yarn
3. 安装 Python 3.9+ 
4. 配置 VS Code 或其他 IDE
5. 安装必要的系统依赖

**验收标准**:
- `cargo --version` 正常输出
- `node --version` 和 `npm --version` 正常输出  
- `python --version` 正常输出
- 能够编译简单的 Rust 程序
- 能够运行简单的 Node.js 程序
- 能够执行 Python 脚本

**注意事项**:
- Windows 环境需要安装 Visual Studio Build Tools
- 确保 Python 路径正确配置
- 验证网络代理设置不影响包管理器

### 1.2 Tauri 项目初始化

**任务ID**: SETUP-002  
**状态**: 待开始  
**前置依赖**: SETUP-001  

**目的**: 创建 Tauri 项目骨架，配置基础架构

**输入**:
- 配置完成的开发环境
- 项目需求规格

**输出**:
- 可运行的 Tauri 项目模板
- 配置文件和构建脚本

**实现要点**:
1. 使用 `npm create tauri-app` 创建项目
2. 选择 React + TypeScript 模板
3. 配置 `tauri.conf.json` 基础设置
4. 设置项目目录结构
5. 配置开发和构建脚本

**验收标准**:
- `npm run tauri dev` 能够启动开发服务器
- 出现默认的 Tauri 窗口界面
- 热重载功能正常工作
- 能够构建生产版本

**注意事项**:
- 确保选择合适的窗口配置
- 设置合理的安全策略
- 预留 Sidecar 配置空间

### 1.3 项目目录结构规划

**任务ID**: SETUP-003  
**状态**: 进行中  
**前置依赖**: SETUP-002  

**目的**: 建立标准化的项目目录结构，为各模块开发做准备

**输入**:
- Tauri 项目模板
- 架构设计文档

**输出**:
- 完整的目录结构
- 各目录的说明文档

**实现要点**:
1. 创建 `python-engines/` 目录结构
2. 创建 `src/` 前端目录结构  
3. 创建 `src-tauri/` 后端目录结构
4. 创建 `tests/` 测试目录结构
5. 创建 `docs/` 文档目录结构
6. 创建 `scripts/` 脚本目录结构

**目录结构详细规划**:
```
LingoSub/
├── .claude/tasks/           # 任务跟踪
├── src-tauri/              # Rust 后端
│   ├── src/
│   │   ├── main.rs
│   │   ├── commands/        # Tauri 命令
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务逻辑
│   │   └── utils/           # 工具函数
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                    # React 前端
│   ├── components/         # React 组件
│   ├── hooks/             # 自定义 Hooks
│   ├── stores/            # 状态管理
│   ├── types/             # TypeScript 类型
│   ├── utils/             # 工具函数
│   └── assets/            # 静态资源
├── python-engines/         # Python Sidecar
│   ├── funasr_engine/     # FunASR 引擎
│   ├── whisper_engine/    # Whisper 引擎
│   ├── netflix_processor/ # Netflix 规范化
│   ├── common/            # 共享模块
│   └── requirements.txt   # Python 依赖
├── tests/                 # 测试文件
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── fixtures/         # 测试数据
├── docs/                 # 文档
│   ├── api/              # API 文档
│   ├── user/             # 用户文档
│   └── dev/              # 开发文档
└── scripts/              # 构建脚本
    ├── build.sh
    ├── test.sh
    └── deploy.sh
```

**验收标准**:
- 所有目录创建完成
- 每个目录包含 README.md 说明
- 目录权限配置正确
- Git 忽略文件配置完整

**注意事项**:
- 保持目录命名一致性
- 预留足够的扩展空间
- 考虑跨平台兼容性

### 1.4 基础配置和依赖管理

**任务ID**: SETUP-004  
**状态**: 待开始  
**前置依赖**: SETUP-003  

**目的**: 配置项目的基础依赖和开发工具

**输入**:
- 完整的目录结构
- 技术栈选择

**输出**:
- 配置完成的包管理文件
- 开发工具配置文件

**实现要点**:
1. 配置 `package.json` 前端依赖
2. 配置 `Cargo.toml` Rust 依赖
3. 配置 `requirements.txt` Python 依赖
4. 设置 ESLint 和 Prettier 配置
5. 设置 TypeScript 配置
6. 配置 Git hooks 和 CI/CD 基础

**关键依赖列表**:

**前端依赖**:
- React 18+
- TypeScript 5+
- Tailwind CSS
- Zustand (状态管理)
- React Query (数据获取)

**Rust 依赖**:
- serde (序列化)
- tokio (异步运行时)
- tauri (框架)
- uuid (唯一标识)
- chrono (时间处理)

**Python 依赖**:
- funasr
- faster-whisper
- pydantic (数据验证)
- asyncio
- logging

**验收标准**:
- 所有依赖安装成功
- 代码格式化工具正常工作
- TypeScript 编译无错误
- 基础的 lint 检查通过

**注意事项**:
- 锁定依赖版本避免兼容性问题
- 设置合理的开发工具配置
- 考虑包大小和构建时间

### 1.5 基础类型定义和接口规范

**任务ID**: SETUP-005  
**状态**: 待开始  
**前置依赖**: SETUP-004  

**目的**: 定义项目核心的数据类型和接口规范

**输入**:
- 项目架构设计
- API 设计文档

**输出**:
- TypeScript 类型定义文件
- Rust 数据结构定义
- Python 数据模型定义
- 接口文档

**实现要点**:
1. 定义 ASR 引擎相关类型
2. 定义任务和结果相关类型
3. 定义 Netflix 规范化相关类型
4. 定义前后端通信协议
5. 定义错误处理类型

**核心类型定义**:

**任务相关**:
```typescript
interface TranscriptionTask {
  id: string;
  file_path: string;
  engines: Engine[];
  status: TaskStatus;
  created_at: string;
  priority: TaskPriority;
}

interface TranscriptionResult {
  task_id: string;
  engine: Engine;
  text: string;
  timestamps: TimeStamp[];
  confidence: number;
  metadata: ResultMetadata;
}
```

**引擎相关**:
```typescript
enum Engine {
  FunASR = "funasr",
  FasterWhisper = "faster-whisper"
}

interface EngineConfig {
  model_size: string;
  language: string;
  options: Record<string, any>;
}
```

**验收标准**:
- 所有核心类型定义完成
- 类型在 TypeScript 中编译通过
- Rust 结构体可以正常序列化
- Python 模型验证正常工作
- 接口文档生成完整

**注意事项**:
- 保持跨语言类型一致性
- 预留扩展字段
- 考虑向后兼容性 