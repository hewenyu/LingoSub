# LingoSub API 接口规范

## 概览

本文档定义了 LingoSub 各模块间的通信接口，包括前端-后端、Rust-Python Sidecar、以及各组件内部接口。

## 1. Tauri 命令接口 (前端 ↔ Rust后端)

### 1.1 任务管理接口

```typescript
// 启动转录任务
interface StartTranscriptionRequest {
  file_path: string;
  engines: ('funasr' | 'faster-whisper')[];
  options: TranscriptionOptions;
}

interface TranscriptionOptions {
  language?: string;
  model_name?: string;
  beam_size?: number;
  temperature?: number;
  enable_vad?: boolean;
  enable_netflix_processing?: boolean;
}

interface TaskResponse {
  task_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  created_at: string;
}
```

```rust
#[tauri::command]
pub async fn start_transcription(
    request: StartTranscriptionRequest
) -> Result<TaskResponse, ApiError>

#[tauri::command] 
pub async fn get_task_status(
    task_id: String
) -> Result<TaskStatus, ApiError>

#[tauri::command]
pub async fn cancel_task(
    task_id: String  
) -> Result<(), ApiError>

#[tauri::command]
pub async fn get_task_result(
    task_id: String
) -> Result<TranscriptionResult, ApiError>
```

### 1.2 文件管理接口

```rust
#[tauri::command]
pub async fn validate_audio_file(
    file_path: String
) -> Result<AudioFileInfo, ApiError>

#[tauri::command]
pub async fn get_supported_formats() -> Result<Vec<String>, ApiError>

#[tauri::command]
pub async fn export_subtitles(
    task_id: String,
    format: SubtitleFormat,
    output_path: String
) -> Result<(), ApiError>
```

### 1.3 系统管理接口

```rust
#[tauri::command]
pub async fn get_engine_status() -> Result<EngineStatus, ApiError>

#[tauri::command]
pub async fn get_system_info() -> Result<SystemInfo, ApiError>

#[tauri::command]
pub async fn update_settings(
    settings: AppSettings
) -> Result<(), ApiError>
```

## 2. Sidecar 通信接口 (Rust ↔ Python)

### 2.1 基础通信协议

```json
// 请求格式
{
  "id": "uuid-string",
  "method": "transcribe|health_check|stop",
  "params": {
    // 方法特定参数
  },
  "timeout": 30000
}

// 响应格式  
{
  "id": "uuid-string",
  "result": {
    // 结果数据
  },
  "error": null | {
    "code": "error_code",
    "message": "error description"
  }
}
```

### 2.2 转录接口

```python
# Python Sidecar 接口
class ASREngine:
    async def transcribe(self, request: TranscribeRequest) -> TranscribeResponse:
        pass
    
    async def health_check(self) -> HealthStatus:
        pass
    
    async def get_capabilities(self) -> EngineCapabilities:
        pass
```

```python
# 转录请求
@dataclass
class TranscribeRequest:
    audio_path: str
    language: Optional[str]
    model_name: Optional[str]
    options: Dict[str, Any]

# 转录响应
@dataclass  
class TranscribeResponse:
    segments: List[SubtitleSegment]
    metadata: TranscriptionMetadata
    processing_time: float
```

### 2.3 字幕段格式

```python
@dataclass
class SubtitleSegment:
    start_time: float  # 秒
    end_time: float    # 秒
    text: str
    confidence: float
    words: Optional[List[WordTiming]]
    language: Optional[str]

@dataclass
class WordTiming:
    word: str
    start_time: float
    end_time: float
    confidence: float
```

## 3. Netflix 处理器接口

### 3.1 规范化接口

```python
class NetflixProcessor:
    def process_subtitles(
        self, 
        subtitles: List[SubtitleSegment],
        language: Language,
        options: NetflixOptions
    ) -> NetflixResult:
        pass

@dataclass
class NetflixOptions:
    max_chars_per_line: int = 16  # 中文
    max_lines: int = 2
    min_duration: float = 0.5
    max_duration: float = 7.0
    max_cps: float = 20.0
    enable_line_break_optimization: bool = True

@dataclass
class NetflixResult:
    processed_subtitles: List[NetflixSubtitle]
    quality_score: float
    compliance_issues: List[ComplianceIssue]
    processing_stats: ProcessingStats
```

## 4. 前端状态管理接口

### 4.1 应用状态结构

```typescript
interface AppState {
  // 任务状态
  tasks: Record<string, TaskState>;
  activeTask: string | null;
  
  // 文件状态  
  files: Record<string, FileState>;
  
  // UI状态
  ui: {
    sidebarOpen: boolean;
    theme: 'light' | 'dark';
    language: string;
    activeTab: string;
  };
  
  // 系统状态
  engines: EngineStatus;
  systemHealth: SystemHealth;
  
  // 用户设置
  settings: UserSettings;
}

interface TaskState {
  id: string;
  file_id: string;
  engines: string[];
  status: TaskStatus;
  progress: number;
  result?: TranscriptionResult;
  error?: string;
  created_at: string;
  updated_at: string;
}
```

### 4.2 操作接口

```typescript
interface AppActions {
  // 任务操作
  startTranscription: (request: StartTranscriptionRequest) => Promise<void>;
  cancelTask: (taskId: string) => Promise<void>;
  removeTask: (taskId: string) => void;
  
  // 文件操作
  addFiles: (files: File[]) => void;
  removeFile: (fileId: string) => void;
  validateFile: (file: File) => Promise<ValidationResult>;
  
  // UI操作
  setActiveTask: (taskId: string) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  
  // 设置操作
  updateSettings: (settings: Partial<UserSettings>) => Promise<void>;
  resetSettings: () => void;
}
```

## 5. 错误处理规范

### 5.1 错误类型定义

```typescript
enum ErrorCode {
  // 文件错误
  FILE_NOT_FOUND = 'FILE_NOT_FOUND',
  FILE_FORMAT_UNSUPPORTED = 'FILE_FORMAT_UNSUPPORTED', 
  FILE_SIZE_TOO_LARGE = 'FILE_SIZE_TOO_LARGE',
  
  // 引擎错误
  ENGINE_NOT_AVAILABLE = 'ENGINE_NOT_AVAILABLE',
  ENGINE_INITIALIZATION_FAILED = 'ENGINE_INITIALIZATION_FAILED',
  TRANSCRIPTION_FAILED = 'TRANSCRIPTION_FAILED',
  
  // 系统错误
  INSUFFICIENT_MEMORY = 'INSUFFICIENT_MEMORY',
  NETWORK_ERROR = 'NETWORK_ERROR',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  
  // 业务错误
  TASK_NOT_FOUND = 'TASK_NOT_FOUND',
  TASK_ALREADY_RUNNING = 'TASK_ALREADY_RUNNING',
  INVALID_CONFIGURATION = 'INVALID_CONFIGURATION'
}

interface ApiError {
  code: ErrorCode;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}
```

## 6. 事件通知接口

### 6.1 实时事件

```typescript
// 任务进度事件
interface TaskProgressEvent {
  task_id: string;
  progress: number;
  stage: 'preprocessing' | 'transcribing' | 'postprocessing';
  estimated_time_remaining?: number;
}

// 系统状态事件
interface SystemStatusEvent {
  engine_status: EngineStatus;
  memory_usage: number;
  cpu_usage: number;
}

// 错误事件
interface ErrorEvent {
  task_id?: string;
  error: ApiError;
  recoverable: boolean;
}
```

## 7. 配置管理接口

### 7.1 用户设置

```typescript
interface UserSettings {
  // 引擎偏好
  preferred_engines: string[];
  default_language: string;
  
  // Netflix 设置
  netflix_compliance: boolean;
  custom_rules: NetflixOptions;
  
  // UI 设置
  theme: 'light' | 'dark';
  language: string;
  auto_save: boolean;
  
  // 性能设置
  max_concurrent_tasks: number;
  gpu_acceleration: boolean;
  memory_limit_mb: number;
}
```

## 8. 测试接口规范

### 8.1 单元测试接口

```typescript
// 测试工具接口
interface TestUtils {
  createMockAudioFile: (duration: number) => File;
  createMockTranscriptionResult: () => TranscriptionResult;
  mockSidecarResponse: (response: any) => void;
}

// 测试数据接口
interface TestFixtures {
  audio_files: Record<string, string>;
  expected_results: Record<string, TranscriptionResult>;
  error_cases: Record<string, ApiError>;
}
```

---

## 版本控制

- **版本**: v1.0.0
- **最后更新**: 2025-01-01
- **状态**: 草案阶段，待评审确认 