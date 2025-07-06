/**
 * 核心业务类型定义
 * 包含项目中使用的基础数据结构和枚举
 */

// 基础标识类型
export type TaskId = string;
export type EngineId = string;
export type FileId = string;
export type UserId = string;

// 语言类型
export enum Language {
  ChineseSimplified = "zh-CN",
  ChineseTraditional = "zh-TW",
  English = "en",
  Japanese = "ja",
  Korean = "ko",
  Auto = "auto",
}

// 音频格式
export enum AudioFormat {
  WAV = "wav",
  MP3 = "mp3",
  MP4 = "mp4",
  M4A = "m4a",
  FLAC = "flac",
  AAC = "aac",
}

// 视频格式
export enum VideoFormat {
  MP4 = "mp4",
  AVI = "avi",
  MOV = "mov",
  MKV = "mkv",
  WMV = "wmv",
}

// 文件类型
export enum FileType {
  Audio = "audio",
  Video = "video",
}

// 时间戳信息
export interface TimeStamp {
  start: number; // 开始时间 (秒)
  end: number; // 结束时间 (秒)
  text: string; // 对应文本
  confidence?: number; // 置信度 (0-1)
}

// 文件信息
export interface FileInfo {
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

// 用户配置
export interface UserConfig {
  language: Language;
  theme: "light" | "dark";
  auto_save: boolean;
  default_engines: EngineId[];
  output_format: "srt" | "ass" | "vtt";
  max_concurrent_tasks: number;
}

// 系统健康状态
export interface SystemHealth {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  gpu_usage?: number;
  status: "healthy" | "warning" | "error";
  timestamp: string;
}

// 错误信息
export interface ErrorInfo {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  stack?: string;
}

// 分页信息
export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// API响应包装
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ErrorInfo;
  pagination?: Pagination;
}

// 进度信息
export interface Progress {
  current: number;
  total: number;
  percentage: number;
  estimated_remaining?: number; // 预计剩余时间(秒)
  status: "pending" | "processing" | "completed" | "error";
}
