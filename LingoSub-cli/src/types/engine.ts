/**
 * ASR引擎相关类型定义
 * 包含引擎配置、状态管理和结果处理
 */

import { Language, TimeStamp } from './core';

// 引擎类型
export enum Engine {
  FunASR = 'funasr',
  FasterWhisper = 'faster-whisper',
}

// 引擎状态
export enum EngineStatus {
  Idle = 'idle',
  Starting = 'starting',
  Running = 'running',
  Stopping = 'stopping',
  Stopped = 'stopped',
  Error = 'error',
}

// 引擎配置基类
export interface BaseEngineConfig {
  engine: Engine;
  language: Language;
  model_size?: string;
  device?: 'cpu' | 'gpu' | 'auto';
  enable_vad?: boolean;
  enable_punctuation?: boolean;
  custom_options?: Record<string, any>;
}

// FunASR引擎配置
export interface FunASRConfig extends BaseEngineConfig {
  engine: Engine.FunASR;
  model_name: string;
  vad_model?: string;
  punc_model?: string;
  use_itn?: boolean;
  hotwords?: string[];
  beam_size?: number;
}

// faster-whisper引擎配置
export interface WhisperConfig extends BaseEngineConfig {
  engine: Engine.FasterWhisper;
  model_size:
    | 'tiny'
    | 'base'
    | 'small'
    | 'medium'
    | 'large-v2'
    | 'large-v3'
    | 'large-v3-turbo';
  compute_type?: 'int8' | 'int16' | 'float16' | 'float32';
  beam_size?: number;
  word_timestamps?: boolean;
  vad_filter?: boolean;
  temperature?: number;
  compression_ratio_threshold?: number;
  logprob_threshold?: number;
  no_speech_threshold?: number;
}

// 引擎配置联合类型
export type EngineConfig = FunASRConfig | WhisperConfig;

// 引擎信息
export interface EngineInfo {
  id: string;
  engine: Engine;
  config: EngineConfig;
  status: EngineStatus;
  pid?: number;
  port?: number;
  health_check_url?: string;
  last_heartbeat?: string;
  error_message?: string;
  performance_stats?: EnginePerformanceStats;
}

// 引擎性能统计
export interface EnginePerformanceStats {
  total_processed: number;
  total_duration: number;
  average_rtf: number; // Real-time Factor
  memory_usage: number;
  cpu_usage: number;
  gpu_usage?: number;
  last_updated: string;
}

// 转录选项
export interface TranscriptionOptions {
  engine: Engine;
  language?: Language;
  enable_word_timestamps?: boolean;
  enable_speaker_diarization?: boolean;
  custom_vocabulary?: string[];
  output_format?: 'text' | 'json' | 'srt';
  chunk_size?: number;
  overlap_size?: number;
}

// 转录结果
export interface TranscriptionResult {
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

// 转录片段
export interface TranscriptionSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  confidence: number;
  words?: WordInfo[];
  speaker?: string;
}

// 词级信息
export interface WordInfo {
  word: string;
  start: number;
  end: number;
  confidence: number;
  probability?: number;
}

// 转录元数据
export interface TranscriptionMetadata {
  engine: Engine;
  model_name: string;
  language: Language;
  audio_duration: number;
  processing_time: number;
  rtf: number;
  total_segments: number;
  average_confidence: number;
  detected_language?: Language;
  language_probability?: number;
  vad_segments?: Array<{ start: number; end: number }>;
}

// 引擎比较结果
export interface EngineComparison {
  primary_engine: Engine;
  secondary_engine: Engine;
  similarity_score: number;
  differences: TextDifference[];
  recommendation: Engine;
  confidence: number;
}

// 文本差异
export interface TextDifference {
  type: 'addition' | 'deletion' | 'substitution';
  position: number;
  primary_text: string;
  secondary_text: string;
  severity: 'low' | 'medium' | 'high';
}
