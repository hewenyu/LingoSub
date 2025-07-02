# 03 Rust 后端协调层开发

## 任务概览

开发 Tauri 的 Rust 后端协调层，实现 Python Sidecar 进程管理、任务调度、结果聚合等核心功能。

## 任务列表

### 3.1 Tauri 命令系统设计

**任务ID**: BACKEND-001  
**状态**: 待开始  
**前置依赖**: ENGINE-001  

**目的**: 建立 Tauri 的命令系统架构，定义前后端通信接口

**输入**:
- 完成的 Python Sidecar 基础架构
- 前端功能需求规格
- API 设计文档

**输出**:
- Tauri 命令接口定义
- 错误处理和响应格式
- 基础的命令路由系统

**实现要点**:
1. 定义核心 Tauri 命令
2. 实现异步命令处理
3. 设计统一的错误处理机制
4. 实现请求验证和参数校验
5. 配置命令权限和安全策略

**核心命令定义**:
```rust
// src-tauri/src/commands/mod.rs
#[derive(Debug, Serialize, Deserialize)]
pub struct TaskRequest {
    pub file_path: String,
    pub engines: Vec<Engine>,
    pub options: TaskOptions,
}

#[tauri::command]
pub async fn start_transcription(
    request: TaskRequest,
    app: AppHandle,
) -> Result<TaskResponse, CommandError> {
    // 启动转录任务
}

#[tauri::command]
pub async fn get_task_status(
    task_id: String,
    app: AppHandle,
) -> Result<TaskStatus, CommandError> {
    // 获取任务状态
}

#[tauri::command]
pub async fn cancel_task(
    task_id: String,
    app: AppHandle,
) -> Result<(), CommandError> {
    // 取消任务
}
```

**命令分类**:
- 任务管理 (启动、停止、查询)
- 文件操作 (上传、验证、格式转换)
- 配置管理 (引擎配置、用户偏好)
- 系统管理 (健康检查、资源监控)

**验收标准**:
- 所有命令能够正确注册和调用
- 异步命令处理正常工作
- 错误处理机制完善
- 参数验证有效
- 前端能够正常调用后端命令

**注意事项**:
- 确保命令的幂等性
- 实现合理的超时机制
- 考虑并发请求的处理

### 3.2 Sidecar 进程管理器

**任务ID**: BACKEND-002  
**状态**: 待开始  
**前置依赖**: BACKEND-001, ENGINE-002, ENGINE-003  

**目的**: 实现 Python Sidecar 进程的生命周期管理和通信

**输入**:
- 完成的 Python 引擎实现
- Tauri 命令系统
- 进程管理需求

**输出**:
- Sidecar 进程管理器
- 进程健康监控系统
- 进程间通信接口

**实现要点**:
1. 实现 Sidecar 进程启动和停止
2. 建立进程间通信机制
3. 实现进程健康检查
4. 处理进程崩溃和重启
5. 管理进程资源使用

**核心实现**:
```rust
// src-tauri/src/services/sidecar_manager.rs
use std::process::{Child, Command};
use tokio::sync::RwLock;

pub struct SidecarManager {
    processes: RwLock<HashMap<String, SidecarProcess>>,
    config: SidecarConfig,
}

#[derive(Debug)]
pub struct SidecarProcess {
    pub id: String,
    pub engine_type: Engine,
    pub child: Child,
    pub status: ProcessStatus,
    pub last_heartbeat: Instant,
}

impl SidecarManager {
    pub async fn start_engine(&self, engine: Engine) -> Result<String, SidecarError> {
        // 启动指定引擎的 Sidecar 进程
    }
    
    pub async fn stop_engine(&self, process_id: &str) -> Result<(), SidecarError> {
        // 停止指定的 Sidecar 进程
    }
    
    pub async fn send_command(&self, process_id: &str, command: SidecarCommand) -> Result<SidecarResponse, SidecarError> {
        // 向 Sidecar 发送命令
    }
    
    pub async fn health_check(&self) -> Vec<ProcessHealth> {
        // 检查所有进程健康状态
    }
}
```

**进程通信协议**:
```rust
#[derive(Debug, Serialize, Deserialize)]
pub struct SidecarCommand {
    pub id: String,
    pub command_type: CommandType,
    pub payload: serde_json::Value,
    pub timeout: Option<u64>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SidecarResponse {
    pub id: String,
    pub status: ResponseStatus,
    pub data: Option<serde_json::Value>,
    pub error: Option<String>,
}
```

**验收标准**:
- 能够成功启动和停止 Python Sidecar 进程
- 进程间通信稳定可靠
- 进程崩溃能够自动检测和重启
- 健康检查功能正常
- 资源使用监控准确
- 支持多个 Sidecar 并行运行

**注意事项**:
- 确保进程优雅关闭
- 处理僵尸进程
- 管理进程启动顺序和依赖

### 3.3 任务调度系统

**任务ID**: BACKEND-003  
**状态**: 待开始  
**前置依赖**: BACKEND-002  

**目的**: 实现智能的任务调度和队列管理系统

**输入**:
- Sidecar 进程管理器
- 任务优先级规则
- 资源使用策略

**输出**:
- 任务调度器
- 队列管理系统
- 负载均衡策略

**实现要点**:
1. 设计任务队列数据结构
2. 实现优先级调度算法
3. 建立资源感知调度
4. 实现任务依赖管理
5. 配置负载均衡策略

**核心实现**:
```rust
// src-tauri/src/services/task_scheduler.rs
use std::collections::{BinaryHeap, HashMap};
use tokio::sync::{RwLock, mpsc};

pub struct TaskScheduler {
    pending_queue: RwLock<BinaryHeap<ScheduledTask>>,
    running_tasks: RwLock<HashMap<String, RunningTask>>,
    completed_tasks: RwLock<HashMap<String, CompletedTask>>,
    resource_monitor: ResourceMonitor,
    sidecar_manager: Arc<SidecarManager>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScheduledTask {
    pub id: String,
    pub priority: TaskPriority,
    pub engines: Vec<Engine>,
    pub file_path: String,
    pub options: TaskOptions,
    pub created_at: Instant,
    pub estimated_duration: Option<Duration>,
}

impl TaskScheduler {
    pub async fn submit_task(&self, task: TranscriptionTask) -> Result<String, SchedulerError> {
        // 提交新任务到队列
    }
    
    pub async fn process_queue(&self) -> Result<(), SchedulerError> {
        // 处理队列中的任务
    }
    
    pub async fn cancel_task(&self, task_id: &str) -> Result<(), SchedulerError> {
        // 取消指定任务
    }
    
    pub async fn get_task_status(&self, task_id: &str) -> Option<TaskStatus> {
        // 获取任务状态
    }
}
```

**调度策略**:
- 优先级调度 (用户交互 > 批量处理)
- 资源感知调度 (GPU/CPU/内存使用率)
- 公平调度 (防止任务饥饿)
- deadline 调度 (紧急任务优先)

**队列管理**:
```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum TaskPriority {
    Low = 1,
    Normal = 2,
    High = 3,
    Critical = 4,
}

#[derive(Debug, Clone)]
pub enum TaskStatus {
    Pending,
    Running { engine: Engine, progress: f32 },
    Completed { result: TranscriptionResult },
    Failed { error: String },
    Cancelled,
}
```

**验收标准**:
- 任务能够按优先级正确调度
- 资源使用率保持在合理范围
- 支持任务取消和状态查询
- 并发任务数量可配置
- 任务完成后资源能够正确释放
- 调度延迟保持在可接受范围

**注意事项**:
- 避免任务饥饿问题
- 合理预估任务执行时间
- 处理任务依赖关系

### 3.4 结果聚合和比较系统

**任务ID**: BACKEND-004  
**状态**: 待开始  
**前置依赖**: BACKEND-003, ENGINE-005  

**目的**: 实现多引擎结果的聚合、比较和质量评估

**输入**:
- 标准化的引擎结果格式
- 任务调度系统
- 结果比较算法

**输出**:
- 结果聚合器
- 引擎比较分析
- 质量评估报告

**实现要点**:
1. 收集多引擎转录结果
2. 实现结果对比算法
3. 生成质量评估报告
4. 提供最佳结果推荐
5. 支持结果合并策略

**核心实现**:
```rust
// src-tauri/src/services/result_aggregator.rs
use std::collections::HashMap;

pub struct ResultAggregator {
    results: RwLock<HashMap<String, TaskResults>>,
    comparator: ResultComparator,
    quality_assessor: QualityAssessor,
}

#[derive(Debug, Clone)]
pub struct TaskResults {
    pub task_id: String,
    pub engine_results: HashMap<Engine, TranscriptionResult>,
    pub comparison: Option<ComparisonReport>,
    pub recommendation: Option<RecommendedResult>,
}

#[derive(Debug, Clone)]
pub struct ComparisonReport {
    pub similarity_score: f32,
    pub confidence_comparison: ConfidenceComparison,
    pub timestamp_accuracy: TimestampAccuracy,
    pub text_differences: Vec<TextDifference>,
    pub quality_metrics: QualityMetrics,
}

impl ResultAggregator {
    pub async fn add_result(&self, task_id: String, engine: Engine, result: TranscriptionResult) -> Result<(), AggregatorError> {
        // 添加引擎结果
    }
    
    pub async fn compare_results(&self, task_id: &str) -> Result<ComparisonReport, AggregatorError> {
        // 比较多引擎结果
    }
    
    pub async fn recommend_best(&self, task_id: &str) -> Result<RecommendedResult, AggregatorError> {
        // 推荐最佳结果
    }
    
    pub async fn merge_results(&self, task_id: &str, strategy: MergeStrategy) -> Result<TranscriptionResult, AggregatorError> {
        // 合并多引擎结果
    }
}
```

**比较算法**:
- 文本相似度计算 (编辑距离、BLEU 等)
- 时间戳对齐分析
- 置信度权重评估
- 语义一致性检查

**质量评估指标**:
```rust
#[derive(Debug, Clone)]
pub struct QualityMetrics {
    pub text_quality: f32,      // 文本质量分数
    pub timestamp_precision: f32, // 时间戳精度
    pub confidence_reliability: f32, // 置信度可靠性
    pub consistency_score: f32,  // 一致性分数
    pub overall_score: f32,     // 综合质量分数
}
```

**验收标准**:
- 能够正确聚合多引擎结果
- 结果比较算法准确有效
- 质量评估指标合理
- 推荐系统能够选择最佳结果
- 支持多种结果合并策略
- 处理性能满足实时要求

**注意事项**:
- 处理引擎结果的时间差异
- 考虑不同引擎的特点和优势
- 避免过度依赖单一指标

### 3.5 配置管理和持久化

**任务ID**: BACKEND-005  
**状态**: 待开始  
**前置依赖**: BACKEND-004  

**目的**: 实现系统配置管理和数据持久化存储

**输入**:
- 用户配置需求
- 系统状态数据
- 缓存策略

**输出**:
- 配置管理系统
- 数据持久化层
- 缓存管理器

**实现要点**:
1. 设计配置文件结构
2. 实现配置热更新
3. 建立数据持久化机制
4. 实现缓存管理
5. 配置备份和恢复

**核心实现**:
```rust
// src-tauri/src/services/config_manager.rs
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub engines: EngineConfigs,
    pub ui: UiConfig,
    pub performance: PerformanceConfig,
    pub netflix: NetflixConfig,
    pub cache: CacheConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EngineConfigs {
    pub funasr: FunASRConfig,
    pub whisper: WhisperConfig,
    pub default_engine: Engine,
    pub parallel_processing: bool,
}

pub struct ConfigManager {
    config_path: PathBuf,
    current_config: RwLock<AppConfig>,
    watchers: Vec<ConfigWatcher>,
}

impl ConfigManager {
    pub async fn load_config(&self) -> Result<AppConfig, ConfigError> {
        // 加载配置文件
    }
    
    pub async fn save_config(&self, config: &AppConfig) -> Result<(), ConfigError> {
        // 保存配置文件
    }
    
    pub async fn update_config<F>(&self, updater: F) -> Result<(), ConfigError>
    where
        F: FnOnce(&mut AppConfig) -> Result<(), ConfigError>,
    {
        // 更新配置
    }
    
    pub async fn reset_to_default(&self) -> Result<(), ConfigError> {
        // 重置为默认配置
    }
}
```

**数据持久化**:
```rust
// src-tauri/src/services/storage.rs
pub struct StorageManager {
    db_path: PathBuf,
    cache: Arc<RwLock<LruCache<String, CachedData>>>,
}

impl StorageManager {
    pub async fn save_task_history(&self, task: &CompletedTask) -> Result<(), StorageError> {
        // 保存任务历史
    }
    
    pub async fn load_task_history(&self, limit: usize) -> Result<Vec<CompletedTask>, StorageError> {
        // 加载任务历史
    }
    
    pub async fn cache_result(&self, key: String, result: TranscriptionResult) -> Result<(), StorageError> {
        // 缓存结果
    }
    
    pub async fn get_cached_result(&self, key: &str) -> Option<TranscriptionResult> {
        // 获取缓存结果
    }
}
```

**配置分类**:
- 引擎配置 (模型路径、参数)
- 界面配置 (主题、布局)
- 性能配置 (并发数、内存限制)
- Netflix 配置 (规范化规则)
- 缓存配置 (大小、过期时间)

**验收标准**:
- 配置文件能够正确加载和保存
- 支持配置热更新
- 数据持久化功能正常
- 缓存机制有效提升性能
- 配置备份和恢复功能完整
- 配置验证防止无效设置

**注意事项**:
- 确保配置文件格式向后兼容
- 处理配置文件损坏的情况
- 合理设置缓存过期策略

### 3.6 监控和日志系统

**任务ID**: BACKEND-006  
**状态**: 待开始  
**前置依赖**: BACKEND-005  

**目的**: 建立完善的系统监控和日志记录机制

**输入**:
- 系统运行数据
- 性能指标需求
- 调试信息需求

**输出**:
- 监控系统
- 日志管理器
- 性能指标收集器

**实现要点**:
1. 实现系统资源监控
2. 建立结构化日志系统
3. 收集性能指标
4. 实现告警机制
5. 提供调试工具

**核心实现**:
```rust
// src-tauri/src/services/monitor.rs
use sysinfo::{System, SystemExt, ProcessExt};

pub struct SystemMonitor {
    system: System,
    metrics_collector: MetricsCollector,
    alerting: AlertingSystem,
}

#[derive(Debug, Clone)]
pub struct SystemMetrics {
    pub cpu_usage: f32,
    pub memory_usage: MemoryUsage,
    pub gpu_usage: Option<GpuUsage>,
    pub disk_usage: DiskUsage,
    pub network_io: NetworkIO,
    pub process_count: usize,
}

#[derive(Debug, Clone)]
pub struct PerformanceMetrics {
    pub task_throughput: f32,
    pub average_processing_time: Duration,
    pub queue_length: usize,
    pub success_rate: f32,
    pub error_rate: f32,
}

impl SystemMonitor {
    pub async fn collect_metrics(&mut self) -> SystemMetrics {
        // 收集系统指标
    }
    
    pub async fn check_health(&self) -> HealthStatus {
        // 检查系统健康状态
    }
    
    pub async fn setup_alerts(&self, rules: Vec<AlertRule>) -> Result<(), MonitorError> {
        // 设置告警规则
    }
}
```

**日志管理**:
```rust
// src-tauri/src/services/logger.rs
use tracing::{info, warn, error, debug};

pub struct LogManager {
    config: LogConfig,
    file_appender: Option<FileAppender>,
    filters: Vec<LogFilter>,
}

#[derive(Debug, Clone)]
pub struct LogConfig {
    pub level: LogLevel,
    pub output: LogOutput,
    pub rotation: LogRotation,
    pub format: LogFormat,
}

impl LogManager {
    pub fn setup_logging(&self) -> Result<(), LogError> {
        // 设置日志系统
    }
    
    pub async fn log_task_event(&self, task_id: &str, event: TaskEvent) {
        // 记录任务事件
    }
    
    pub async fn log_performance(&self, metrics: &PerformanceMetrics) {
        // 记录性能数据
    }
    
    pub async fn get_logs(&self, filter: LogFilter) -> Result<Vec<LogEntry>, LogError> {
        // 获取日志记录
    }
}
```

**监控指标**:
- 系统资源使用率
- 任务处理性能
- 错误率和成功率
- Sidecar 进程状态
- 内存泄漏检测

**验收标准**:
- 系统监控数据准确及时
- 日志记录完整有序
- 性能指标收集正常
- 告警机制及时有效
- 日志文件轮转正常
- 监控数据可视化友好

**注意事项**:
- 避免监控系统影响主要功能性能
- 合理设置日志级别和大小限制
- 确保敏感信息不被记录 