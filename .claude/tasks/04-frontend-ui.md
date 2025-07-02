# 04 Tauri 前端界面开发

## 任务概览

开发基于 React + TypeScript 的现代化桌面端用户界面，实现直观的字幕工作流和专业的编辑功能。

## 任务列表

### 4.1 基础UI架构和组件库

**任务ID**: FRONTEND-001  
**状态**: 待开始  
**前置依赖**: SETUP-005, BACKEND-001  

**目的**: 建立前端应用的基础架构和可复用组件库

**输入**:
- Tauri 命令接口定义
- UI设计规范和风格指南
- 组件需求分析

**输出**:
- React 应用基础架构
- 通用组件库
- 主题和样式系统

**实现要点**:
1. 配置 React Router 路由系统
2. 建立 Zustand 状态管理
3. 实现 Tailwind CSS 主题系统
4. 开发通用 UI 组件库
5. 配置国际化 (i18n) 支持

**核心架构**:
```typescript
// src/App.tsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="app-container">
          <Routes>
            <Route path="/" element={<MainWorkspace />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
          <Toaster position="top-right" />
        </div>
      </Router>
    </QueryClientProvider>
  );
}
```

**状态管理架构**:
```typescript
// src/stores/app-store.ts
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

interface AppState {
  // 任务状态
  tasks: Record<string, TaskState>;
  activeTask: string | null;
  
  // UI 状态
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  language: string;
  
  // 系统状态
  engineStatus: EngineStatus;
  systemHealth: SystemHealth;
}

export const useAppStore = create<AppState>()(
  subscribeWithSelector((set, get) => ({
    // 状态和操作方法
  }))
);
```

**通用组件库**:
- Button, Input, Select 等基础组件
- Modal, Tooltip, Dropdown 等交互组件
- Progress, Loading, StatusIndicator 等状态组件
- FileUploader, AudioPlayer 等业务组件

**验收标准**:
- React 应用能够正常启动和渲染
- 路由导航功能正常
- 状态管理响应及时
- 组件库样式一致美观
- 主题切换功能正常
- 响应式布局适配良好

**注意事项**:
- 确保组件的可访问性 (a11y)
- 优化组件渲染性能
- 保持设计系统的一致性

### 4.2 主工作区界面

**任务ID**: FRONTEND-002  
**状态**: 待开始  
**前置依赖**: FRONTEND-001, BACKEND-002  

**目的**: 实现主要的工作界面，包括文件管理、任务控制和进度展示

**输入**:
- 基础UI架构
- Sidecar 进程管理接口
- 工作流程设计

**输出**:
- 主工作区组件
- 文件管理界面
- 任务控制面板

**实现要点**:
1. 设计响应式布局结构
2. 实现文件拖拽上传
3. 开发任务控制面板
4. 建立实时进度显示
5. 集成系统状态监控

**主工作区布局**:
```typescript
// src/components/MainWorkspace.tsx
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

export function MainWorkspace() {
  const { tasks, startTranscription } = useAppStore();
  
  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach(file => {
      startTranscription({
        file,
        engines: ['funasr', 'faster-whisper'],
        options: getDefaultOptions()
      });
    });
  }, [startTranscription]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.wav', '.mp3', '.m4a', '.flac'],
      'video/*': ['.mp4', '.avi', '.mov']
    }
  });

  return (
    <div className="main-workspace">
      <Sidebar />
      <div className="workspace-content">
        <FileDropZone {...getRootProps()} />
        <TaskControlPanel />
        <ProgressDashboard />
      </div>
      <StatusBar />
    </div>
  );
}
```

**文件管理功能**:
```typescript
// src/components/FileManager.tsx
export function FileManager() {
  const { files, removeFile, previewFile } = useFileStore();
  
  return (
    <div className="file-manager">
      <div className="file-list">
        {files.map(file => (
          <FileCard
            key={file.id}
            file={file}
            onRemove={() => removeFile(file.id)}
            onPreview={() => previewFile(file.id)}
          />
        ))}
      </div>
      <FileUploader />
    </div>
  );
}
```

**任务控制面板**:
```typescript
// src/components/TaskControlPanel.tsx
export function TaskControlPanel() {
  const { activeTask, pauseTask, resumeTask, cancelTask } = useTaskStore();
  
  if (!activeTask) return <EmptyState />;
  
  return (
    <div className="task-control-panel">
      <TaskInfo task={activeTask} />
      <EngineSelector />
      <ControlButtons
        onPause={() => pauseTask(activeTask.id)}
        onResume={() => resumeTask(activeTask.id)}
        onCancel={() => cancelTask(activeTask.id)}
      />
      <ProgressIndicator progress={activeTask.progress} />
    </div>
  );
}
```

**验收标准**:
- 文件拖拽上传功能正常
- 任务控制按钮响应及时
- 进度显示准确实时
- 布局在不同屏幕尺寸下正常
- 支持多文件批量处理
- 错误状态显示清晰

**注意事项**:
- 处理大文件上传的用户体验
- 确保实时数据更新不影响性能
- 提供清晰的视觉反馈

### 4.3 字幕编辑器

**任务ID**: FRONTEND-003  
**状态**: 待开始  
**前置依赖**: FRONTEND-002, BACKEND-004  

**目的**: 开发专业的字幕编辑器，支持时间轴编辑和文本修改

**输入**:
- 转录结果数据格式
- 字幕编辑需求规格
- Netflix 规范化标准

**输出**:
- 字幕编辑器组件
- 时间轴控制器
- 文本编辑功能

**实现要点**:
1. 实现可视化时间轴
2. 开发双击编辑功能
3. 支持快捷键操作
4. 实现自动保存机制
5. 集成 Netflix 规范检查

**字幕编辑器核心**:
```typescript
// src/components/SubtitleEditor.tsx
import { useVirtualizer } from '@tanstack/react-virtual';

export function SubtitleEditor() {
  const { subtitles, updateSubtitle, activeIndex } = useSubtitleStore();
  const parentRef = useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: subtitles.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
  });

  return (
    <div className="subtitle-editor">
      <TimelineHeader />
      <div ref={parentRef} className="subtitle-list">
        <div style={{ height: virtualizer.getTotalSize() }}>
          {virtualizer.getVirtualItems().map(virtualItem => (
            <SubtitleItem
              key={virtualItem.key}
              index={virtualItem.index}
              subtitle={subtitles[virtualItem.index]}
              isActive={virtualItem.index === activeIndex}
              onUpdate={updateSubtitle}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
```

**字幕条目组件**:
```typescript
// src/components/SubtitleItem.tsx
export function SubtitleItem({ subtitle, isActive, onUpdate }: SubtitleItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(subtitle.text);
  
  const handleDoubleClick = () => {
    setIsEditing(true);
  };
  
  const handleSave = () => {
    onUpdate(subtitle.id, { text: editText });
    setIsEditing(false);
  };
  
  return (
    <div className={`subtitle-item ${isActive ? 'active' : ''}`}>
      <TimeCode
        startTime={subtitle.startTime}
        endTime={subtitle.endTime}
        onChange={(times) => onUpdate(subtitle.id, times)}
      />
      <div className="subtitle-text" onDoubleClick={handleDoubleClick}>
        {isEditing ? (
          <TextEditor
            value={editText}
            onChange={setEditText}
            onSave={handleSave}
            onCancel={() => setIsEditing(false)}
          />
        ) : (
          <span>{subtitle.text}</span>
        )}
      </div>
      <NetflixComplianceIndicator subtitle={subtitle} />
    </div>
  );
}
```

**时间轴控制**:
```typescript
// src/components/Timeline.tsx
export function Timeline() {
  const { currentTime, duration, subtitles } = usePlayerStore();
  const { setCurrentTime } = usePlayerActions();
  
  return (
    <div className="timeline">
      <TimelineRuler duration={duration} />
      <TimelineTrack>
        {subtitles.map(subtitle => (
          <TimelineSegment
            key={subtitle.id}
            subtitle={subtitle}
            currentTime={currentTime}
            onClick={() => setCurrentTime(subtitle.startTime)}
          />
        ))}
      </TimelineTrack>
      <PlayheadIndicator currentTime={currentTime} />
    </div>
  );
}
```

**验收标准**:
- 字幕列表渲染性能良好 (虚拟化)
- 双击编辑功能流畅
- 时间轴同步准确
- 快捷键操作响应及时
- Netflix 规范检查准确
- 自动保存功能可靠

**注意事项**:
- 处理长字幕列表的性能优化
- 确保编辑操作的撤销重做
- 维护时间轴与音频的同步

### 4.4 引擎结果对比界面

**任务ID**: FRONTEND-004  
**状态**: 待开始  
**前置依赖**: FRONTEND-003, BACKEND-004  

**目的**: 实现多引擎结果的对比展示和分析功能

**输入**:
- 多引擎转录结果
- 结果比较分析数据
- 质量评估指标

**输出**:
- 结果对比组件
- 差异高亮显示
- 质量分析图表

**实现要点**:
1. 实现并排对比视图
2. 开发差异高亮算法
3. 展示质量评估指标
4. 提供最佳结果推荐
5. 支持结果合并操作

**结果对比界面**:
```typescript
// src/components/ResultComparison.tsx
export function ResultComparison() {
  const { comparisonData, selectBestResult, mergeResults } = useComparisonStore();
  
  if (!comparisonData) return <NoComparisonData />;
  
  return (
    <div className="result-comparison">
      <ComparisonHeader data={comparisonData} />
      <div className="comparison-content">
        <EngineResultPanel
          engine="funasr"
          result={comparisonData.results.funasr}
          differences={comparisonData.differences.funasr}
        />
        <EngineResultPanel
          engine="faster-whisper"
          result={comparisonData.results.whisper}
          differences={comparisonData.differences.whisper}
        />
      </div>
      <ComparisonActions
        onSelectBest={selectBestResult}
        onMerge={mergeResults}
      />
      <QualityMetricsChart metrics={comparisonData.metrics} />
    </div>
  );
}
```

**差异高亮组件**:
```typescript
// src/components/DiffHighlight.tsx
export function DiffHighlight({ text, differences }: DiffHighlightProps) {
  const renderWithHighlights = () => {
    let result = [];
    let lastIndex = 0;
    
    differences.forEach((diff, index) => {
      // 添加未修改的文本
      if (diff.start > lastIndex) {
        result.push(
          <span key={`normal-${index}`}>
            {text.slice(lastIndex, diff.start)}
          </span>
        );
      }
      
      // 添加高亮的差异文本
      result.push(
        <span
          key={`diff-${index}`}
          className={`diff-highlight diff-${diff.type}`}
          title={diff.description}
        >
          {text.slice(diff.start, diff.end)}
        </span>
      );
      
      lastIndex = diff.end;
    });
    
    // 添加剩余文本
    if (lastIndex < text.length) {
      result.push(
        <span key="final">
          {text.slice(lastIndex)}
        </span>
      );
    }
    
    return result;
  };
  
  return <div className="diff-text">{renderWithHighlights()}</div>;
}
```

**质量指标图表**:
```typescript
// src/components/QualityMetricsChart.tsx
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';

export function QualityMetricsChart({ metrics }: QualityMetricsProps) {
  const chartData = [
    { name: 'FunASR', confidence: metrics.funasr.confidence, quality: metrics.funasr.quality },
    { name: 'Whisper', confidence: metrics.whisper.confidence, quality: metrics.whisper.quality },
  ];
  
  return (
    <div className="quality-metrics-chart">
      <h3>质量对比</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <XAxis dataKey="name" />
          <YAxis />
          <Bar dataKey="confidence" fill="#8884d8" name="置信度" />
          <Bar dataKey="quality" fill="#82ca9d" name="质量分数" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

**验收标准**:
- 对比视图布局清晰易读
- 差异高亮显示准确
- 质量指标图表直观
- 结果选择操作流畅
- 支持结果导出功能
- 响应式设计适配良好

**注意事项**:
- 处理长文本对比的性能
- 确保差异算法的准确性
- 提供清晰的视觉区分

### 4.5 设置和配置界面

**任务ID**: FRONTEND-005  
**状态**: 待开始  
**前置依赖**: FRONTEND-004, BACKEND-005  

**目的**: 实现系统设置和用户配置管理界面

**输入**:
- 配置管理接口
- 用户偏好设置需求
- 系统参数配置

**输出**:
- 设置页面组件
- 配置表单组件
- 偏好管理功能

**实现要点**:
1. 设计分类设置页面
2. 实现表单验证机制
3. 支持配置导入导出
4. 提供预设配置方案
5. 实现设置搜索功能

**设置页面结构**:
```typescript
// src/components/SettingsPage.tsx
export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('engines');
  
  const settingsTabs = [
    { id: 'engines', label: '引擎设置', icon: Cpu },
    { id: 'ui', label: '界面设置', icon: Monitor },
    { id: 'performance', label: '性能设置', icon: Zap },
    { id: 'netflix', label: 'Netflix规范', icon: Film },
    { id: 'about', label: '关于', icon: Info },
  ];
  
  return (
    <div className="settings-page">
      <SettingsNavigation
        tabs={settingsTabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
      <div className="settings-content">
        {activeTab === 'engines' && <EngineSettings />}
        {activeTab === 'ui' && <UISettings />}
        {activeTab === 'performance' && <PerformanceSettings />}
        {activeTab === 'netflix' && <NetflixSettings />}
        {activeTab === 'about' && <AboutSettings />}
      </div>
    </div>
  );
}
```

**引擎设置组件**:
```typescript
// src/components/settings/EngineSettings.tsx
export function EngineSettings() {
  const { config, updateConfig } = useConfigStore();
  const { register, handleSubmit, formState: { errors } } = useForm();
  
  const onSubmit = (data: EngineConfigData) => {
    updateConfig('engines', data);
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="engine-settings">
      <SettingsSection title="FunASR 配置">
        <FormField
          label="模型路径"
          {...register('funasr.modelPath', { required: true })}
          error={errors.funasr?.modelPath}
        />
        <FormField
          label="设备"
          type="select"
          options={[
            { value: 'cuda', label: 'GPU (CUDA)' },
            { value: 'cpu', label: 'CPU' }
          ]}
          {...register('funasr.device')}
        />
        <FormField
          label="批量大小"
          type="number"
          {...register('funasr.batchSize', { min: 1, max: 32 })}
        />
      </SettingsSection>
      
      <SettingsSection title="Whisper 配置">
        <FormField
          label="模型大小"
          type="select"
          options={[
            { value: 'large-v3', label: 'Large V3' },
            { value: 'medium', label: 'Medium' },
            { value: 'large-v3-turbo', label: 'Turbo' }
          ]}
          {...register('whisper.modelSize')}
        />
        <FormField
          label="计算类型"
          type="select"
          options={[
            { value: 'float16', label: 'Float16' },
            { value: 'int8_float16', label: 'Int8 Float16' }
          ]}
          {...register('whisper.computeType')}
        />
      </SettingsSection>
      
      <SettingsActions>
        <Button type="submit" variant="primary">保存设置</Button>
        <Button type="button" variant="secondary" onClick={resetToDefault}>
          恢复默认
        </Button>
      </SettingsActions>
    </form>
  );
}
```

**配置导入导出**:
```typescript
// src/components/settings/ConfigManager.tsx
export function ConfigManager() {
  const { exportConfig, importConfig } = useConfigActions();
  
  const handleExport = async () => {
    const config = await exportConfig();
    const blob = new Blob([JSON.stringify(config, null, 2)], {
      type: 'application/json'
    });
    downloadFile(blob, 'lingosub-config.json');
  };
  
  const handleImport = async (file: File) => {
    try {
      const content = await file.text();
      const config = JSON.parse(content);
      await importConfig(config);
      toast.success('配置导入成功');
    } catch (error) {
      toast.error('配置文件格式错误');
    }
  };
  
  return (
    <div className="config-manager">
      <Button onClick={handleExport}>导出配置</Button>
      <FileUploader
        accept=".json"
        onUpload={handleImport}
        label="导入配置"
      />
    </div>
  );
}
```

**验收标准**:
- 设置页面导航流畅
- 表单验证规则正确
- 配置保存和加载正常
- 导入导出功能完整
- 设置搜索功能有效
- 预设方案切换正常

**注意事项**:
- 确保配置验证的完整性
- 处理配置冲突和兼容性
- 提供清晰的错误提示

### 4.6 用户体验优化

**任务ID**: FRONTEND-006  
**状态**: 待开始  
**前置依赖**: FRONTEND-005  

**目的**: 优化用户界面和交互体验，提升应用的易用性

**输入**:
- 完整的UI组件
- 用户反馈和测试结果
- 性能分析数据

**输出**:
- 优化的用户界面
- 改进的交互体验
- 性能优化实现

**实现要点**:
1. 实现加载状态和骨架屏
2. 优化大数据渲染性能
3. 改进错误处理和提示
4. 增强快捷键支持
5. 实现无障碍访问功能

**加载状态管理**:
```typescript
// src/components/LoadingStates.tsx
export function SkeletonLoader({ type }: { type: 'subtitle' | 'task' | 'comparison' }) {
  const skeletonConfig = {
    subtitle: { rows: 10, height: 60 },
    task: { rows: 3, height: 80 },
    comparison: { rows: 5, height: 120 }
  };
  
  const config = skeletonConfig[type];
  
  return (
    <div className="skeleton-loader">
      {Array.from({ length: config.rows }).map((_, index) => (
        <div
          key={index}
          className="skeleton-item animate-pulse"
          style={{ height: config.height }}
        />
      ))}
    </div>
  );
}

export function LoadingOverlay({ isVisible, message }: LoadingOverlayProps) {
  if (!isVisible) return null;
  
  return (
    <div className="loading-overlay">
      <div className="loading-content">
        <Spinner size="large" />
        <p className="loading-message">{message}</p>
      </div>
    </div>
  );
}
```

**性能优化**:
```typescript
// src/hooks/useVirtualization.ts
export function useVirtualization<T>(
  items: T[],
  estimateSize: number,
  overscan = 5
) {
  const parentRef = useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateSize,
    overscan,
  });
  
  return {
    parentRef,
    virtualItems: virtualizer.getVirtualItems(),
    totalSize: virtualizer.getTotalSize(),
  };
}

// src/hooks/useDebounce.ts
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  
  return debouncedValue;
}
```

**快捷键支持**:
```typescript
// src/hooks/useKeyboardShortcuts.ts
export function useKeyboardShortcuts() {
  const { playPause, seekForward, seekBackward } = usePlayerActions();
  const { saveSubtitles, exportSRT } = useSubtitleActions();
  
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 's':
            event.preventDefault();
            saveSubtitles();
            break;
          case 'e':
            event.preventDefault();
            exportSRT();
            break;
        }
      } else {
        switch (event.key) {
          case ' ':
            event.preventDefault();
            playPause();
            break;
          case 'ArrowLeft':
            seekBackward(5);
            break;
          case 'ArrowRight':
            seekForward(5);
            break;
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);
}
```

**错误边界处理**:
```typescript
// src/components/ErrorBoundary.tsx
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo);
    // 发送错误报告
    this.props.onError?.(error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>出现了一些问题</h2>
          <p>应用遇到了未预期的错误</p>
          <Button onClick={() => this.setState({ hasError: false, error: null })}>
            重试
          </Button>
          <details className="error-details">
            <summary>错误详情</summary>
            <pre>{this.state.error?.stack}</pre>
          </details>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

**无障碍访问**:
```typescript
// src/components/AccessibleComponents.tsx
export function AccessibleButton({ children, ariaLabel, ...props }: AccessibleButtonProps) {
  return (
    <button
      {...props}
      aria-label={ariaLabel}
      className={`accessible-button ${props.className || ''}`}
    >
      {children}
    </button>
  );
}

export function ScreenReaderOnly({ children }: { children: React.ReactNode }) {
  return (
    <span className="sr-only">
      {children}
    </span>
  );
}
```

**验收标准**:
- 加载状态显示及时自然
- 大列表滚动性能流畅
- 错误处理用户友好
- 快捷键功能完整可用
- 无障碍访问支持良好
- 整体用户体验流畅

**注意事项**:
- 平衡功能完整性和性能
- 确保错误恢复机制可靠
- 考虑不同用户群体的需求 