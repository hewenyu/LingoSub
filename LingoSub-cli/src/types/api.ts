/**
 * API通信协议类型定义
 * 包含前后端通信、Sidecar通信和外部API接口
 */

import { ApiResponse, ErrorInfo, TaskId } from './core';
import { Engine } from './engine';
import { TaskInfo, CreateTaskRequest } from './task';
import { NetflixProcessingOptions } from './netflix';

// Tauri命令类型
export type TauriCommand =
  | 'start_transcription'
  | 'get_task_status'
  | 'cancel_task'
  | 'get_task_list'
  | 'get_engine_status'
  | 'get_system_health'
  | 'update_config'
  | 'get_history'
  | 'export_results'
  | 'import_file'
  | 'validate_file';

// Tauri命令请求
export interface TauriRequest<T = any> {
  command: TauriCommand;
  payload: T;
  request_id?: string;
  timeout?: number;
}

// Tauri命令响应
export interface TauriResponse<T = any> extends ApiResponse<T> {
  request_id?: string;
  execution_time?: number;
}

// 启动转录请求
export interface StartTranscriptionRequest extends CreateTaskRequest {
  file_path: string;
  engines: Engine[];
  options: StartTranscriptionOptions;
}

// 启动转录选项
export interface StartTranscriptionOptions {
  language?: string;
  output_format: 'srt' | 'ass' | 'vtt' | 'txt';
  enable_netflix_processing?: boolean;
  enable_comparison?: boolean;
  netflix_options?: NetflixProcessingOptions;
  notification_webhook?: string;
  custom_config?: Record<string, any>;
}

// 启动转录响应
export interface StartTranscriptionResponse {
  task_id: TaskId;
  estimated_duration?: number;
  queue_position?: number;
}

// 获取任务状态请求
export interface GetTaskStatusRequest {
  task_id: TaskId;
  include_progress?: boolean;
  include_logs?: boolean;
}

// 获取任务状态响应
export interface GetTaskStatusResponse {
  task: TaskInfo;
  progress_details?: ProgressDetails;
  logs?: LogEntry[];
}

// 进度详情
export interface ProgressDetails {
  current_stage: string;
  stage_progress: number;
  total_stages: number;
  current_engine?: Engine;
  engine_progress?: Record<Engine, number>;
  estimated_remaining: number;
  throughput?: number;
}

// 日志条目
export interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  context?: Record<string, any>;
  source?: string;
}

// 取消任务请求
export interface CancelTaskRequest {
  task_id: TaskId;
  reason?: string;
  force?: boolean;
}

// 获取任务列表请求
export interface GetTaskListRequest {
  status?: string[];
  engines?: Engine[];
  limit?: number;
  offset?: number;
  sort_by?: 'created_at' | 'updated_at' | 'priority';
  sort_order?: 'asc' | 'desc';
}

// 获取任务列表响应
export interface GetTaskListResponse {
  tasks: TaskInfo[];
  total: number;
  has_more: boolean;
}

// 获取引擎状态响应
export interface GetEngineStatusResponse {
  engines: EngineStatusInfo[];
  system_load: number;
  available_capacity: number;
}

// 引擎状态信息
export interface EngineStatusInfo {
  engine: Engine;
  status: 'idle' | 'running' | 'error';
  current_tasks: number;
  max_capacity: number;
  performance_metrics: EnginePerformanceMetrics;
  last_heartbeat: string;
  error_message?: string;
}

// 引擎性能指标
export interface EnginePerformanceMetrics {
  cpu_usage: number;
  memory_usage: number;
  gpu_usage?: number;
  queue_length: number;
  average_processing_time: number;
  success_rate: number;
  last_updated: string;
}

// 系统健康检查响应
export interface SystemHealthResponse {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  components: ComponentHealth[];
  resource_usage: ResourceUsage;
  alerts: SystemAlert[];
}

// 组件健康状态
export interface ComponentHealth {
  component: string;
  status: 'healthy' | 'warning' | 'error';
  message?: string;
  last_check: string;
  response_time?: number;
}

// 资源使用情况
export interface ResourceUsage {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  gpu_usage?: number;
  network_usage?: number;
  active_connections: number;
}

// 系统警报
export interface SystemAlert {
  id: string;
  type: 'warning' | 'error' | 'critical';
  component: string;
  message: string;
  timestamp: string;
  resolved: boolean;
  resolution_time?: string;
}

// Sidecar通信协议
export interface SidecarMessage {
  id: string;
  type: SidecarMessageType;
  payload: any;
  timestamp: string;
  timeout?: number;
}

// Sidecar消息类型
export type SidecarMessageType =
  | 'command'
  | 'response'
  | 'heartbeat'
  | 'error'
  | 'notification'
  | 'shutdown';

// Sidecar命令
export interface SidecarCommand {
  command: string;
  parameters: Record<string, any>;
  request_id: string;
  timeout?: number;
}

// Sidecar响应
export interface SidecarResponse {
  request_id: string;
  status: 'success' | 'error';
  data?: any;
  error?: ErrorInfo;
  processing_time?: number;
}

// Sidecar心跳
export interface SidecarHeartbeat {
  engine: Engine;
  status: 'alive' | 'busy' | 'idle';
  load: number;
  memory_usage: number;
  last_task?: string;
  queue_size: number;
}

// 文件验证请求
export interface ValidateFileRequest {
  file_path: string;
  expected_format?: string;
  check_integrity?: boolean;
}

// 文件验证响应
export interface ValidateFileResponse {
  is_valid: boolean;
  file_info: FileValidationInfo;
  issues: FileValidationIssue[];
}

// 文件验证信息
export interface FileValidationInfo {
  format: string;
  size: number;
  duration?: number;
  sample_rate?: number;
  channels?: number;
  bit_rate?: number;
  codec?: string;
  metadata?: Record<string, any>;
}

// 文件验证问题
export interface FileValidationIssue {
  type: 'warning' | 'error';
  code: string;
  message: string;
  details?: Record<string, any>;
}

// 导出结果请求
export interface ExportResultsRequest {
  task_ids: TaskId[];
  format: 'json' | 'csv' | 'excel' | 'pdf';
  include_metadata?: boolean;
  output_path?: string;
}

// 导出结果响应
export interface ExportResultsResponse {
  export_id: string;
  file_path: string;
  file_size: number;
  format: string;
  created_at: string;
  expires_at?: string;
}

// 实时更新事件
export interface RealtimeEvent {
  event_type: string;
  data: any;
  timestamp: string;
  source?: string;
}

// 实时更新监听选项
export interface RealtimeSubscriptionOptions {
  events: string[];
  filter?: Record<string, any>;
  debounce?: number;
  buffer_size?: number;
}

// WebSocket消息
export interface WebSocketMessage {
  type: 'subscribe' | 'unsubscribe' | 'event' | 'heartbeat' | 'error';
  payload: any;
  timestamp: string;
}

// 批量操作请求
export interface BatchOperationRequest {
  operation: 'cancel' | 'retry' | 'delete' | 'export';
  task_ids: TaskId[];
  options?: Record<string, any>;
}

// 批量操作响应
export interface BatchOperationResponse {
  operation_id: string;
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  errors: Array<{
    task_id: TaskId;
    error: ErrorInfo;
  }>;
}

// 配置更新请求
export interface UpdateConfigRequest {
  section: 'user' | 'engine' | 'system' | 'netflix';
  config: Record<string, any>;
  validate?: boolean;
}

// 配置更新响应
export interface UpdateConfigResponse {
  updated: boolean;
  validation_errors?: string[];
  restart_required?: boolean;
  affected_components?: string[];
}
