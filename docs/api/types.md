# LingoSub 类型定义文档

## 概述

本文档描述了 LingoSub 项目中使用的核心数据类型和接口规范。项目采用跨语言类型定义系统，确保 TypeScript、Rust 和 Python 之间的类型一致性。

## 基础类型

### 标识符类型

```typescript
type TaskId = string;        // 任务唯一标识
type EngineId = string;      // 引擎标识
type FileId = string;        // 文件标识
type UserId = string;        // 用户标识
```

### 枚举类型

#### 语言类型
```typescript
enum Language {
  ChineseSimplified = "zh-CN",
  ChineseTraditional = "zh-TW",
  English = "en",
  Japanese = "ja",
  Korean = "ko",
  Auto = "auto"
}
```

#### 文件格式
```typescript
// 音频格式
enum AudioFormat {
  WAV = "wav",
  MP3 = "mp3",
  MP4 = "mp4",
  M4A = "m4a",
  FLAC = "flac",
  AAC = "aac"
}

// 视频格式
enum VideoFormat {
  MP4 = "mp4",
  AVI = "avi",
  MOV = "mov",
  MKV = "mkv",
  WMV = "wmv"
}
```

#### 引擎类型
```typescript
enum Engine {
  FunASR = "funasr",
  FasterWhisper = "faster-whisper"
}
```

#### 任务状态
```typescript
enum TaskStatus {
  Pending = "pending",
  Queued = "queued",
  Running = "running",
  Paused = "paused",
  Completed = "completed",
  Failed = "failed",
  Cancelled = "cancelled"
}
```

## 核心数据结构

### 时间戳信息
```typescript
interface TimeStamp {
  start: number;           // 开始时间(秒)
  end: number;             // 结束时间(秒)
  text: string;            // 对应文本
  confidence?: number;     // 置信度(0-1)
}
```

### 文件信息
```typescript
interface FileInfo {
  id: FileId;
  name: string;
  path: string;
  size: number;
  type: FileType;
  format: AudioFormat | VideoFormat;
  duration?: number;
  created_at: string;
  modified_at: string;
  metadata?: Record<string, any>;
}
```

### 进度信息
```typescript
interface Progress {
  current: number;
  total: number;
  percentage: number;
  estimated_remaining?: number;  // 预计剩余时间(秒)
  status: "pending" | "processing" | "completed" | "error";
}
```

### 错误信息
```typescript
interface ErrorInfo {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  stack?: string;
}
```

## 引擎相关类型

### 引擎配置
```typescript
// 基础配置
interface BaseEngineConfig {
  engine: Engine;
  language: Language;
  model_size?: string;
  device?: "cpu" | "gpu" | "auto";
  enable_vad?: boolean;
  enable_punctuation?: boolean;
  custom_options?: Record<string, any>;
}

// FunASR配置
interface FunASRConfig extends BaseEngineConfig {
  engine: Engine.FunASR;
  model_name: string;
  vad_model?: string;
  punc_model?: string;
  use_itn?: boolean;
  hotwords?: string[];
  beam_size?: number;
}

// Whisper配置
interface WhisperConfig extends BaseEngineConfig {
  engine: Engine.FasterWhisper;
  model_size: "tiny" | "base" | "small" | "medium" | "large-v2" | "large-v3" | "large-v3-turbo";
  compute_type?: "int8" | "int16" | "float16" | "float32";
  beam_size?: number;
  word_timestamps?: boolean;
  vad_filter?: boolean;
  temperature?: number;
}
```

### 转录结果
```typescript
interface TranscriptionResult {
  task_id: string;
  engine: Engine;
  language: Language;
  text: string;
  timestamps: TimeStamp[];
  segments: TranscriptionSegment[];
  confidence: number;
  processing_time: number;
  metadata: TranscriptionMetadata;
}
```

## 任务管理类型

### 任务信息
```typescript
interface TaskInfo {
  id: TaskId;
  file_id: FileId;
  type: TaskType;
  status: TaskStatus;
  priority: TaskPriority;
  engines: Engine[];
  options: TaskOptions;
  progress: Progress;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  error?: ErrorInfo;
  estimated_duration?: number;
  actual_duration?: number;
  name?: string;
  description?: string;
}
```

### 任务选项
```typescript
interface TaskOptions {
  output_format: "srt" | "ass" | "vtt" | "txt";
  language?: string;
  enable_netflix_processing?: boolean;
  enable_comparison?: boolean;
  custom_config?: Record<string, any>;
  notification_settings?: NotificationSettings;
}
```

## Netflix 规范化类型

### Netflix 规则
```typescript
interface NetflixRules {
  language: Language;
  max_chars_per_line: number;
  max_lines: number;
  min_duration: number;
  max_duration: number;
  max_cps: number;
  min_gap: number;
  punctuation_rules: Record<string, string>;
  line_break_chars: string[];
  forbidden_chars: string[];
}
```

### 处理结果
```typescript
interface NetflixProcessingResult {
  task_id: TaskId;
  input_segments: RawSubtitleSegment[];
  output_segments: NetflixSubtitleSegment[];
  processing_stats: ProcessingStats;
  quality_report: QualityReport;
  compliance_report: ComplianceReport;
  optimization_log: OptimizationLog[];
  output_files: NetflixOutputFile[];
  processing_time: number;
  created_at: string;
}
```

## API 通信类型

### 通用响应格式
```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ErrorInfo;
  pagination?: Pagination;
}
```

### Tauri 命令
```typescript
type TauriCommand = 
  | "start_transcription"
  | "get_task_status"
  | "cancel_task"
  | "get_task_list"
  | "get_engine_status"
  | "get_system_health"
  | "update_config"
  | "get_history"
  | "export_results"
  | "import_file"
  | "validate_file";
```

## 跨语言映射

### TypeScript ↔ Rust
- `string` ↔ `String`
- `number` ↔ `f64` / `u32` / `i32`
- `boolean` ↔ `bool`
- `Array<T>` ↔ `Vec<T>`
- `Record<K, V>` ↔ `HashMap<K, V>`
- `T | null` ↔ `Option<T>`

### TypeScript ↔ Python
- `string` ↔ `str`
- `number` ↔ `float` / `int`
- `boolean` ↔ `bool`
- `Array<T>` ↔ `List[T]`
- `Record<K, V>` ↔ `Dict[K, V]`
- `T | undefined` ↔ `Optional[T]`

## 使用示例

### 创建任务
```typescript
const request: CreateTaskRequest = {
  file_path: "/path/to/audio.wav",
  engines: [Engine.FunASR, Engine.FasterWhisper],
  options: {
    output_format: "srt",
    language: "zh-CN",
    enable_netflix_processing: true,
    enable_comparison: true
  },
  priority: TaskPriority.Normal
};
```

### 处理结果
```typescript
const result: TranscriptionResult = {
  task_id: "task-123",
  engine: Engine.FunASR,
  language: Language.ChineseSimplified,
  text: "转录文本内容",
  timestamps: [
    { start: 0.0, end: 2.5, text: "转录文本", confidence: 0.95 }
  ],
  confidence: 0.95,
  processing_time: 5.2,
  metadata: { /* ... */ }
};
```

## 验证规则

1. **时间戳验证**: `start < end`，`confidence` 在 `[0, 1]` 范围内
2. **文件路径验证**: 必须是有效的文件路径
3. **语言代码验证**: 必须符合 ISO 639-1 标准
4. **引擎配置验证**: 根据引擎类型验证配置参数
5. **Netflix规则验证**: 字符数、时长、CPS等必须符合规范

## 扩展性

类型定义系统支持以下扩展：
- 新增引擎类型和配置
- 扩展任务选项和元数据
- 添加新的文件格式支持
- 自定义验证规则
- 多语言规范支持 