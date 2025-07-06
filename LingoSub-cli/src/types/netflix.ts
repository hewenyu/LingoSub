/**
 * Netflix规范化相关类型定义
 * 包含字幕规范、处理规则和质量控制
 */

import { Language, TaskId } from "./core";

// Netflix字幕规范
export interface NetflixRules {
  language: Language;
  max_chars_per_line: number;
  max_lines: number;
  min_duration: number; // 最小持续时间(秒)
  max_duration: number; // 最大持续时间(秒)
  max_cps: number; // 最大字符每秒
  min_gap: number; // 最小间隔(秒)
  punctuation_rules: Record<string, string>;
  line_break_chars: string[];
  forbidden_chars: string[];
  number_format_rules: NumberFormatRules;
  time_format_rules: TimeFormatRules;
}

// 数字格式规则
export interface NumberFormatRules {
  spell_out_below: number;
  use_commas: boolean;
  decimal_places: number;
  currency_format: string;
  percentage_format: string;
}

// 时间格式规则
export interface TimeFormatRules {
  use_24_hour: boolean;
  show_seconds: boolean;
  am_pm_format: string;
  date_format: string;
}

// Netflix处理选项
export interface NetflixProcessingOptions {
  language: Language;
  enable_auto_segmentation: boolean;
  enable_punctuation_correction: boolean;
  enable_number_formatting: boolean;
  enable_time_formatting: boolean;
  enable_line_breaking: boolean;
  enable_timing_adjustment: boolean;
  custom_rules?: Partial<NetflixRules>;
  quality_threshold: number;
}

// 原始字幕片段
export interface RawSubtitleSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  confidence: number;
  speaker?: string;
  metadata?: Record<string, any>;
}

// Netflix处理后的字幕片段
export interface NetflixSubtitleSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  lines: string[];
  chars_per_line: number[];
  cps: number;
  duration: number;
  compliance_status: ComplianceStatus;
  applied_rules: string[];
  quality_score: number;
  original_text?: string;
  confidence: number;
}

// 合规性状态
export interface ComplianceStatus {
  is_compliant: boolean;
  violations: ComplianceViolation[];
  warnings: ComplianceWarning[];
  score: number;
}

// 合规性违规
export interface ComplianceViolation {
  rule: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  position?: number;
  suggested_fix?: string;
}

// 合规性警告
export interface ComplianceWarning {
  rule: string;
  description: string;
  position?: number;
  suggestion?: string;
}

// 文本分析结果
export interface TextAnalysisResult {
  segments: TextSegment[];
  break_points: BreakPoint[];
  semantic_units: SemanticUnit[];
  readability_score: number;
  complexity_score: number;
}

// 文本片段
export interface TextSegment {
  text: string;
  start_pos: number;
  end_pos: number;
  type: 'sentence' | 'phrase' | 'word';
  importance: number;
  can_break: boolean;
}

// 断点信息
export interface BreakPoint {
  position: number;
  type: 'natural' | 'forced' | 'optimal';
  score: number;
  reason: string;
  context_before: string;
  context_after: string;
}

// 语义单元
export interface SemanticUnit {
  text: string;
  start: number;
  end: number;
  type: 'subject' | 'predicate' | 'object' | 'modifier';
  importance: number;
  dependencies: number[];
}

// 时间轴优化结果
export interface TimelineOptimizationResult {
  original_segments: NetflixSubtitleSegment[];
  optimized_segments: NetflixSubtitleSegment[];
  adjustments: TimelineAdjustment[];
  quality_improvement: number;
  compliance_improvement: number;
}

// 时间轴调整
export interface TimelineAdjustment {
  segment_id: number;
  type: 'start_time' | 'end_time' | 'duration' | 'gap';
  original_value: number;
  adjusted_value: number;
  reason: string;
  impact_score: number;
}

// Netflix处理结果
export interface NetflixProcessingResult {
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

// 处理统计
export interface ProcessingStats {
  total_segments: number;
  processed_segments: number;
  merged_segments: number;
  split_segments: number;
  adjusted_segments: number;
  violations_fixed: number;
  warnings_remaining: number;
  quality_score: number;
  compliance_rate: number;
}

// 质量报告
export interface QualityReport {
  overall_score: number;
  readability_score: number;
  timing_score: number;
  formatting_score: number;
  consistency_score: number;
  issues: QualityIssue[];
  recommendations: string[];
}

// 质量问题
export interface QualityIssue {
  type: 'timing' | 'formatting' | 'content' | 'consistency';
  severity: 'low' | 'medium' | 'high';
  description: string;
  segment_id?: number;
  position?: number;
  suggested_fix?: string;
}

// 合规性报告
export interface ComplianceReport {
  overall_compliance: boolean;
  compliance_rate: number;
  violations_by_rule: Record<string, number>;
  critical_violations: ComplianceViolation[];
  fixed_violations: ComplianceViolation[];
  remaining_violations: ComplianceViolation[];
  recommendations: string[];
}

// 优化日志
export interface OptimizationLog {
  timestamp: string;
  operation: string;
  segment_id: number;
  before: string;
  after: string;
  reason: string;
  impact: 'positive' | 'negative' | 'neutral';
}

// Netflix输出文件
export interface NetflixOutputFile {
  path: string;
  format: 'srt' | 'ass' | 'vtt' | 'dfxp';
  size: number;
  segment_count: number;
  compliance_score: number;
  quality_score: number;
  checksum: string;
  created_at: string;
}

// 自定义规则
export interface CustomRule {
  id: string;
  name: string;
  description: string;
  language: Language;
  rule_type: 'character_limit' | 'timing' | 'formatting' | 'content';
  condition: RuleCondition;
  action: RuleAction;
  priority: number;
  enabled: boolean;
}

// 规则条件
export interface RuleCondition {
  type: 'text_length' | 'duration' | 'cps' | 'pattern' | 'position';
  operator: '>' | '<' | '=' | '!=' | '>=' | '<=' | 'contains' | 'matches';
  value: number | string;
  context?: string;
}

// 规则动作
export interface RuleAction {
  type: 'split' | 'merge' | 'adjust_timing' | 'replace_text' | 'flag_violation';
  parameters: Record<string, any>;
  fallback?: RuleAction;
}

// 规则引擎配置
export interface RuleEngineConfig {
  language: Language;
  standard_rules: NetflixRules;
  custom_rules: CustomRule[];
  processing_order: string[];
  quality_thresholds: QualityThresholds;
}

// 质量阈值
export interface QualityThresholds {
  minimum_compliance: number;
  minimum_quality: number;
  maximum_violations: number;
  critical_violation_limit: number;
}
