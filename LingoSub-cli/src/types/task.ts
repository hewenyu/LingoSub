/**
 * 任务管理相关类型定义
 * 包含任务状态、队列管理和执行结果
 */

import { TaskId, FileId, Progress, ErrorInfo } from './core';
import { Engine, EngineConfig, TranscriptionResult } from './engine';

// 任务状态
export enum TaskStatus {
  Pending = 'pending',
  Queued = 'queued',
  Running = 'running',
  Paused = 'paused',
  Completed = 'completed',
  Failed = 'failed',
  Cancelled = 'cancelled',
}

// 任务优先级
export enum TaskPriority {
  Low = 'low',
  Normal = 'normal',
  High = 'high',
  Critical = 'critical',
}

// 任务类型
export enum TaskType {
  SingleEngine = 'single_engine',
  MultiEngine = 'multi_engine',
  Comparison = 'comparison',
  Batch = 'batch',
}

// 任务创建请求
export interface CreateTaskRequest {
  file_path: string;
  engines: Engine[];
  options: TaskOptions;
  priority?: TaskPriority;
  name?: string;
  description?: string;
}

// 任务选项
export interface TaskOptions {
  output_format: 'srt' | 'ass' | 'vtt' | 'txt';
  language?: string;
  enable_netflix_processing?: boolean;
  enable_comparison?: boolean;
  custom_config?: Record<string, any>;
  notification_settings?: NotificationSettings;
}

// 通知设置
export interface NotificationSettings {
  on_completion: boolean;
  on_error: boolean;
  email_notifications?: boolean;
  webhook_url?: string;
}

// 任务信息
export interface TaskInfo {
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

// 任务执行上下文
export interface TaskExecutionContext {
  task_id: TaskId;
  file_path: string;
  engines: EngineExecutionInfo[];
  workspace_path: string;
  temp_files: string[];
  start_time: string;
  timeout?: number;
}

// 引擎执行信息
export interface EngineExecutionInfo {
  engine: Engine;
  config: EngineConfig;
  status: TaskStatus;
  pid?: number;
  progress: Progress;
  result?: TranscriptionResult;
  error?: ErrorInfo;
  start_time?: string;
  end_time?: string;
}

// 任务结果
export interface TaskResult {
  task_id: TaskId;
  status: TaskStatus;
  results: TranscriptionResult[];
  comparison?: EngineComparison;
  netflix_output?: NetflixProcessingResult;
  output_files: OutputFile[];
  execution_time: number;
  created_at: string;
  metadata: TaskMetadata;
}

// 输出文件
export interface OutputFile {
  path: string;
  format: string;
  size: number;
  checksum?: string;
  created_at: string;
}

// 任务元数据
export interface TaskMetadata {
  file_info: {
    name: string;
    size: number;
    duration: number;
    format: string;
  };
  processing_info: {
    total_time: number;
    cpu_time: number;
    memory_peak: number;
    gpu_usage?: number;
  };
  quality_metrics: {
    average_confidence: number;
    processing_speed: number;
    error_rate?: number;
  };
}

// 任务队列状态
export interface TaskQueue {
  pending: TaskInfo[];
  running: TaskInfo[];
  completed: TaskInfo[];
  failed: TaskInfo[];
  total_capacity: number;
  current_load: number;
  estimated_wait_time: number;
}

// 任务统计
export interface TaskStatistics {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  cancelled_tasks: number;
  average_processing_time: number;
  success_rate: number;
  engine_usage: Record<Engine, number>;
  daily_stats: DailyStats[];
}

// 日统计
export interface DailyStats {
  date: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  processing_time: number;
}

// 批量任务请求
export interface BatchTaskRequest {
  file_paths: string[];
  engines: Engine[];
  options: TaskOptions;
  priority?: TaskPriority;
  name?: string;
  description?: string;
}

// 批量任务结果
export interface BatchTaskResult {
  batch_id: string;
  tasks: TaskResult[];
  total_files: number;
  successful_files: number;
  failed_files: number;
  total_time: number;
  created_at: string;
  completed_at?: string;
}

// 引擎比较结果 (重新导出)
export interface EngineComparison {
  primary_engine: Engine;
  secondary_engine: Engine;
  similarity_score: number;
  differences: TextDifference[];
  recommendation: Engine;
  confidence: number;
}

// 文本差异 (重新导出)
export interface TextDifference {
  type: 'addition' | 'deletion' | 'substitution';
  position: number;
  primary_text: string;
  secondary_text: string;
  severity: 'low' | 'medium' | 'high';
}

// Netflix处理结果 (前向声明)
export interface NetflixProcessingResult {
  task_id: TaskId;
  original_segments: number;
  processed_segments: number;
  optimization_applied: string[];
  quality_score: number;
  compliance_issues: string[];
  processing_time: number;
}
