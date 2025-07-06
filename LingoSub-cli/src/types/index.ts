/**
 * LingoSub 类型定义统一导出
 * 提供项目中所有类型定义的统一入口
 */

// 核心类型
export * from "./core";

// 引擎相关类型
export * from "./engine";

// 任务管理类型 - 排除重复的类型
export type {
  TaskStatus,
  TaskPriority,
  TaskType,
  CreateTaskRequest,
  TaskOptions,
  NotificationSettings,
  TaskInfo,
  TaskExecutionContext,
  EngineExecutionInfo,
  TaskResult,
  OutputFile,
  TaskMetadata,
  TaskQueue,
  TaskStatistics,
  DailyStats,
  BatchTaskRequest,
  BatchTaskResult,
  NetflixProcessingResult
} from "./task";

// Netflix规范类型
export * from "./netflix";

// API通信类型
export * from "./api"; 