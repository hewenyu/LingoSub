# LingoSub 通信协议规范

## 概述

LingoSub 采用多层通信架构：
- **前端 ↔ Rust后端**: Tauri命令系统
- **Rust后端 ↔ Python Sidecar**: JSON-RPC over TCP/stdin
- **内部组件**: 事件驱动异步通信

## Tauri 命令系统

### 命令格式

```typescript
interface TauriRequest<T = any> {
  command: TauriCommand;
  payload: T;
  request_id?: string;
  timeout?: number;
}

interface TauriResponse<T = any> extends ApiResponse<T> {
  request_id?: string;
  execution_time?: number;
}
```

### 核心命令

#### 1. 启动转录任务
```typescript
// 命令: start_transcription
// 请求
interface StartTranscriptionRequest {
  file_path: string;
  engines: Engine[];
  options: StartTranscriptionOptions;
}

interface StartTranscriptionOptions {
  language?: string;
  output_format: "srt" | "ass" | "vtt" | "txt";
  enable_netflix_processing?: boolean;
  enable_comparison?: boolean;
  netflix_options?: NetflixProcessingOptions;
  notification_webhook?: string;
  custom_config?: Record<string, any>;
}

// 响应
interface StartTranscriptionResponse {
  task_id: TaskId;
  estimated_duration?: number;
  queue_position?: number;
}
```

#### 2. 获取任务状态
```typescript
// 命令: get_task_status
// 请求
interface GetTaskStatusRequest {
  task_id: TaskId;
  include_progress?: boolean;
  include_logs?: boolean;
}

// 响应
interface GetTaskStatusResponse {
  task: TaskInfo;
  progress_details?: ProgressDetails;
  logs?: LogEntry[];
}
```

#### 3. 取消任务
```typescript
// 命令: cancel_task
// 请求
interface CancelTaskRequest {
  task_id: TaskId;
  reason?: string;
  force?: boolean;
}

// 响应: void (成功时) 或 ErrorInfo (失败时)
```

#### 4. 获取任务列表
```typescript
// 命令: get_task_list
// 请求
interface GetTaskListRequest {
  status?: string[];
  engines?: Engine[];
  limit?: number;
  offset?: number;
  sort_by?: "created_at" | "updated_at" | "priority";
  sort_order?: "asc" | "desc";
}

// 响应
interface GetTaskListResponse {
  tasks: TaskInfo[];
  total: number;
  has_more: boolean;
}
```

#### 5. 获取引擎状态
```typescript
// 命令: get_engine_status
// 请求: void

// 响应
interface GetEngineStatusResponse {
  engines: EngineStatusInfo[];
  system_load: number;
  available_capacity: number;
}
```

#### 6. 系统健康检查
```typescript
// 命令: get_system_health
// 请求: void

// 响应
interface SystemHealthResponse {
  overall_status: "healthy" | "degraded" | "unhealthy";
  components: ComponentHealth[];
  resource_usage: ResourceUsage;
  alerts: SystemAlert[];
}
```

### 错误处理

所有命令都使用统一的错误格式：

```typescript
interface ErrorInfo {
  code: string;           // 错误代码 (如 "TASK_NOT_FOUND")
  message: string;        // 用户友好的错误消息
  details?: Record<string, any>;  // 详细错误信息
  timestamp: string;      // ISO时间戳
  stack?: string;         // 调试用堆栈信息
}
```

常见错误代码：
- `TASK_NOT_FOUND`: 任务不存在
- `INVALID_FILE_FORMAT`: 不支持的文件格式
- `ENGINE_NOT_AVAILABLE`: 引擎不可用
- `INSUFFICIENT_RESOURCES`: 系统资源不足
- `VALIDATION_ERROR`: 参数验证失败
- `TIMEOUT_ERROR`: 操作超时
- `INTERNAL_ERROR`: 内部错误

## Sidecar 通信协议

### JSON-RPC 格式

Rust后端与Python Sidecar之间使用JSON-RPC 2.0协议通信。

#### 请求格式
```json
{
  "jsonrpc": "2.0",
  "method": "transcribe",
  "params": {
    "file_path": "/path/to/audio.wav",
    "config": {
      "engine": "funasr",
      "language": "zh-CN",
      "model_name": "paraformer-zh"
    },
    "options": {
      "enable_vad": true,
      "chunk_size": 30
    }
  },
  "id": "req-123"
}
```

#### 响应格式
```json
// 成功响应
{
  "jsonrpc": "2.0",
  "result": {
    "task_id": "task-456",
    "text": "转录结果文本",
    "timestamps": [...],
    "confidence": 0.95,
    "processing_time": 5.2
  },
  "id": "req-123"
}

// 错误响应
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "details": "模型加载失败",
      "engine": "funasr"
    }
  },
  "id": "req-123"
}
```

### Sidecar 方法

#### 1. 转录方法
```typescript
// 方法: transcribe
interface TranscribeParams {
  file_path: string;
  config: EngineConfig;
  options: TranscriptionOptions;
}

interface TranscribeResult extends TranscriptionResult {
  // 继承 TranscriptionResult 的所有字段
}
```

#### 2. 健康检查
```typescript
// 方法: health_check
// 参数: void

interface HealthCheckResult {
  status: "healthy" | "degraded" | "error";
  engine: Engine;
  memory_usage: number;
  model_loaded: boolean;
  last_activity: string;
}
```

#### 3. 配置更新
```typescript
// 方法: update_config
interface UpdateConfigParams {
  config: EngineConfig;
  restart_required?: boolean;
}

interface UpdateConfigResult {
  success: boolean;
  applied_config: EngineConfig;
  restart_required: boolean;
}
```

#### 4. 取消任务
```typescript
// 方法: cancel_task
interface CancelTaskParams {
  task_id: TaskId;
  force?: boolean;
}

interface CancelTaskResult {
  cancelled: boolean;
  task_id: TaskId;
}
```

### 心跳机制

Sidecar定期发送心跳消息：

```json
{
  "jsonrpc": "2.0",
  "method": "heartbeat",
  "params": {
    "engine": "funasr",
    "status": "alive",
    "load": 0.3,
    "memory_usage": 1024.5,
    "queue_size": 2,
    "last_task": "task-789"
  }
}
```

## 事件系统

### 实时事件

系统使用事件驱动架构，支持实时状态更新：

```typescript
interface RealtimeEvent {
  event_type: string;
  data: any;
  timestamp: string;
  source?: string;
}
```

常见事件类型：
- `task_created`: 任务创建
- `task_started`: 任务开始
- `task_progress`: 进度更新
- `task_completed`: 任务完成
- `task_failed`: 任务失败
- `engine_status_changed`: 引擎状态变化
- `system_alert`: 系统警报

### 事件订阅

```typescript
// 订阅选项
interface RealtimeSubscriptionOptions {
  events: string[];              // 要订阅的事件类型
  filter?: Record<string, any>;  // 事件过滤条件
  debounce?: number;             // 防抖延迟(毫秒)
  buffer_size?: number;          // 缓冲区大小
}

// 订阅示例
const subscription = {
  events: ["task_progress", "task_completed"],
  filter: { task_id: "task-123" },
  debounce: 500
};
```

## 批量操作

### 批量任务请求
```typescript
interface BatchTaskRequest {
  file_paths: string[];
  engines: Engine[];
  options: TaskOptions;
  priority?: TaskPriority;
  name?: string;
  description?: string;
}

interface BatchTaskResult {
  batch_id: string;
  tasks: TaskResult[];
  total_files: number;
  successful_files: number;
  failed_files: number;
  total_time: number;
  created_at: string;
  completed_at?: string;
}
```

### 批量操作
```typescript
interface BatchOperationRequest {
  operation: "cancel" | "retry" | "delete" | "export";
  task_ids: TaskId[];
  options?: Record<string, any>;
}

interface BatchOperationResponse {
  operation_id: string;
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  errors: Array<{
    task_id: TaskId;
    error: ErrorInfo;
  }>;
}
```

## 安全性

### 认证
- 本地应用无需额外认证
- Sidecar通信通过本地端口，限制本机访问
- API密钥用于外部服务集成

### 数据验证
- 所有输入参数严格验证
- 文件路径验证防止路径遍历
- 配置参数范围检查

### 错误处理
- 敏感信息不在错误消息中暴露
- 详细错误仅在开发模式下显示
- 错误日志集中管理

## 性能考虑

### 超时设置
- 命令默认超时：30秒
- 长任务(转录)超时：10分钟
- 健康检查超时：5秒
- 心跳间隔：30秒

### 连接管理
- Sidecar连接池
- 自动重连机制
- 连接健康监控
- 优雅关闭处理

### 缓存策略
- 任务状态缓存：1分钟
- 引擎状态缓存：30秒
- 系统健康缓存：10秒
- 文件信息缓存：5分钟

## 调试支持

### 日志格式
```json
{
  "timestamp": "2024-12-19T10:30:00.000Z",
  "level": "INFO",
  "component": "sidecar_manager",
  "message": "Engine started successfully",
  "context": {
    "engine": "funasr",
    "pid": 12345,
    "port": 8001
  }
}
```

### 调试命令
- `get_debug_info`: 获取调试信息
- `enable_verbose_logging`: 启用详细日志
- `dump_state`: 导出当前状态
- `force_gc`: 强制垃圾回收

### 监控指标
- 请求响应时间
- 错误率统计
- 资源使用情况
- 队列长度
- 处理吞吐量 