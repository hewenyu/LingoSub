# 02 Python ASR 引擎 Sidecar 开发

## 任务概览

开发 FunASR 和 faster-whisper 两个 ASR 引擎的 Python Sidecar 进程，实现标准化的接口和高效的音频处理能力。

## 任务列表

### 2.1 Python Sidecar 基础架构

**任务ID**: ENGINE-001  
**状态**: 已完成 ✅  
**完成时间**: 2025-07-06  
**前置依赖**: SETUP-005 ✅  

**目的**: 建立 Python Sidecar 进程的基础架构和通信机制

**输入**:
- 完成的项目基础架构
- ASR 引擎技术调研结果
- 接口规范文档

**输出**:
- ✅ Python Sidecar 基础框架 (`python-engines/common/`)
- ✅ 标准化的进程通信接口 (`communication.py`)
- ✅ 基础的错误处理和日志系统 (`logger.py`)

**实现要点**:
1. ✅ 创建统一的 Sidecar 基类 (`base_engine.py`)
2. ✅ 实现 JSON-RPC 通信协议 (`communication.py`)
3. ✅ 设计异步任务处理架构 (`lifecycle.py`)
4. ✅ 实现进程生命周期管理 (`ProcessManager`)
5. ✅ 配置日志和监控系统 (`logger.py`)

**核心代码结构**:
```python
# python-engines/common/base_engine.py
class BaseSidecarEngine:
    def __init__(self, config: EngineConfig):
        pass
    
    async def process_request(self, request: TranscriptionRequest) -> TranscriptionResponse:
        pass
    
    async def health_check(self) -> HealthStatus:
        pass

# python-engines/common/communication.py  
class SidecarCommunicator:
    async def listen_for_commands(self):
        pass
    
    async def send_response(self, response: dict):
        pass
```

**验收标准**:
- ✅ Sidecar 进程能够启动和正常退出
- ✅ 能够接收和响应 JSON-RPC 请求
- ✅ 健康检查接口正常工作
- ✅ 日志输出格式规范
- ✅ 异常情况能够正确处理和上报

**测试验证**:
- ✅ 所有集成测试通过
- ✅ 基础引擎功能正常
- ✅ 错误处理机制完善
- ✅ 指标收集和监控正常
- ✅ 进程生命周期管理正常

**注意事项**:
- 确保进程间通信的稳定性
- 实现优雅的进程关闭机制
- 考虑内存泄漏和资源清理

### 2.2 FunASR 引擎集成

**任务ID**: ENGINE-002  
**状态**: 待开始  
**前置依赖**: ENGINE-001 ✅  

**目的**: 集成 FunASR 语音识别引擎，实现中文优化的转录能力

**输入**:
- ✅ Sidecar 基础架构
- FunASR 技术文档和示例
- 中文语音测试数据

**输出**:
- FunASR 引擎 Sidecar 实现
- 支持多种 FunASR 模型切换
- 时间戳和置信度输出

**实现要点**:
1. 集成 FunASR AutoModel 接口
2. 实现模型自动下载和缓存
3. 支持 Paraformer 和 SenseVoice 模型
4. 实现批量和流式处理
5. 优化 GPU 内存使用

**核心功能实现**:
```python
# python-engines/funasr_engine/engine.py
class FunASREngine(BaseSidecarEngine):
    def __init__(self, config: FunASRConfig):
        self.model = AutoModel(
            model=config.model_name,
            vad_model=config.vad_model,
            punc_model=config.punc_model,
            device=config.device
        )
    
    async def transcribe(self, audio_path: str, options: dict) -> TranscriptionResult:
        result = self.model.generate(
            input=audio_path,
            merge_vad=True,
            use_itn=True,
            **options
        )
        return self._format_result(result)
```

**支持的模型配置**:
- paraformer-zh (中文通用)
- SenseVoiceSmall (多语言)
- paraformer-zh-streaming (实时)
- 自定义热词支持

**验收标准**:
- 能够加载和初始化 FunASR 模型
- 支持 WAV、MP3、MP4 等音频格式
- 输出包含准确的时间戳信息
- 置信度计算正确
- 支持中文标点符号和数字规范化
- 处理速度满足实时要求 (RTF < 0.5)

**注意事项**:
- 模型下载失败的降级策略
- GPU 显存不足时的处理
- 长音频文件的分段处理

### 2.3 faster-whisper 引擎集成

**任务ID**: ENGINE-003  
**状态**: 待开始  
**前置依赖**: ENGINE-001  

**目的**: 集成 faster-whisper 语音识别引擎，实现高速多语言转录能力

**输入**:
- Sidecar 基础架构
- faster-whisper 技术文档
- 多语言语音测试数据

**输出**:
- faster-whisper 引擎 Sidecar 实现
- 支持多种 Whisper 模型
- 词级时间戳输出

**实现要点**:
1. 集成 WhisperModel 接口
2. 实现模型自动下载和管理
3. 支持 large-v3、turbo 等模型
4. 实现批量推理优化
5. 支持语言自动检测

**核心功能实现**:
```python
# python-engines/whisper_engine/engine.py
class WhisperEngine(BaseSidecarEngine):
    def __init__(self, config: WhisperConfig):
        self.model = WhisperModel(
            model_size_or_path=config.model_size,
            device=config.device,
            compute_type=config.compute_type
        )
    
    async def transcribe(self, audio_path: str, options: dict) -> TranscriptionResult:
        segments, info = self.model.transcribe(
            audio_path,
            beam_size=options.get('beam_size', 5),
            word_timestamps=True,
            vad_filter=True,
            **options
        )
        return self._format_segments(segments, info)
```

**支持的模型配置**:
- large-v3 (最高质量)
- medium (平衡)
- large-v3-turbo (高速)
- 自定义模型路径

**验收标准**:
- 能够加载和初始化 Whisper 模型
- 支持多种音频格式和采样率
- 词级时间戳准确度高
- 支持语言自动检测
- 批量处理性能优秀
- VAD 过滤功能正常工作

**注意事项**:
- 模型文件的本地缓存管理
- 不同计算精度的性能权衡
- 批量推理的内存管理

### 2.4 音频预处理模块

**任务ID**: ENGINE-004  
**状态**: 待开始  
**前置依赖**: ENGINE-002, ENGINE-003  

**目的**: 实现音频文件的预处理和格式转换，提高 ASR 准确率

**输入**:
- 各种格式的音频文件
- 音频质量评估需求

**输出**:
- 标准化的音频预处理模块
- 音频质量检测和优化
- 支持多种输入格式

**实现要点**:
1. 音频格式转换和重采样
2. 音频质量检测和增强
3. VAD (语音活动检测)
4. 音频分段和合并
5. 噪声检测和处理

**核心功能实现**:
```python
# python-engines/common/audio_processor.py
class AudioProcessor:
    def __init__(self, config: AudioConfig):
        pass
    
    def preprocess(self, input_path: str) -> ProcessedAudio:
        # 格式转换、重采样、增强
        pass
    
    def detect_segments(self, audio: np.ndarray) -> List[Segment]:
        # VAD 分段检测
        pass
    
    def enhance_quality(self, audio: np.ndarray) -> np.ndarray:
        # 音频质量增强
        pass
```

**支持的音频格式**:
- WAV (PCM, 各种采样率)
- MP3 (各种比特率)
- MP4/M4A (音频轨道提取)
- FLAC (无损压缩)
- OGG (开源格式)

**验收标准**:
- 支持所有主流音频格式
- 音频转换无质量损失
- VAD 分段准确率 > 95%
- 处理速度满足实时要求
- 音频质量评估准确
- 内存使用优化

**注意事项**:
- 大文件的流式处理
- 音频编解码器的依赖管理
- 跨平台兼容性

### 2.5 结果格式标准化

**任务ID**: ENGINE-005  
**状态**: 待开始  
**前置依赖**: ENGINE-002, ENGINE-003, ENGINE-004  

**目的**: 统一不同 ASR 引擎的输出格式，便于后续处理和比较

**输入**:
- FunASR 原始输出格式
- faster-whisper 原始输出格式
- Netflix 规范化需求

**输出**:
- 标准化的结果格式转换器
- 引擎结果对比工具
- 质量评估指标

**实现要点**:
1. 定义统一的结果数据结构
2. 实现 FunASR 结果格式转换
3. 实现 Whisper 结果格式转换
4. 添加置信度归一化
5. 实现结果质量评估

**标准化结果格式**:
```python
@dataclass
class StandardTranscriptionResult:
    task_id: str
    engine: str
    text: str
    segments: List[TranscriptionSegment]
    language: Optional[str]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]

@dataclass  
class TranscriptionSegment:
    start_time: float  # 秒
    end_time: float    # 秒
    text: str
    words: List[WordTimestamp]
    confidence: float
```

**格式转换实现**:
```python
# python-engines/common/result_formatter.py
class ResultFormatter:
    @staticmethod
    def format_funasr_result(raw_result: dict, task_id: str) -> StandardTranscriptionResult:
        pass
    
    @staticmethod
    def format_whisper_result(segments: Iterator, info: dict, task_id: str) -> StandardTranscriptionResult:
        pass
    
    @staticmethod
    def compare_results(results: List[StandardTranscriptionResult]) -> ComparisonReport:
        pass
```

**验收标准**:
- 所有引擎结果能够转换为统一格式
- 时间戳精度保持一致 (毫秒级)
- 置信度计算标准化
- 结果对比功能正常
- 支持增量结果更新
- 内存占用优化

**注意事项**:
- 不同引擎的时间戳基准对齐
- 置信度计算方法的差异处理
- 长文本的分段策略

### 2.6 性能优化和测试

**任务ID**: ENGINE-006  
**状态**: 待开始  
**前置依赖**: ENGINE-005  

**目的**: 优化 Python Sidecar 的性能和稳定性，建立完善的测试体系

**输入**:
- 完整的引擎实现
- 性能基准要求
- 测试数据集

**输出**:
- 性能优化的引擎实现
- 完整的测试套件
- 性能基准报告

**实现要点**:
1. 内存使用优化
2. 并发处理能力提升
3. 模型加载和切换优化
4. 错误恢复机制完善
5. 压力测试和基准测试

**性能优化策略**:
```python
# python-engines/common/performance.py
class PerformanceOptimizer:
    def __init__(self):
        self.model_cache = ModelCache()
        self.memory_pool = MemoryPool()
        self.worker_pool = WorkerPool()
    
    async def optimize_batch_processing(self, tasks: List[Task]) -> List[Result]:
        # 批量处理优化
        pass
    
    def monitor_resources(self) -> ResourceMetrics:
        # 资源监控
        pass
```

**测试覆盖范围**:
- 单元测试 (各模块功能)
- 集成测试 (端到端流程)
- 性能测试 (速度和内存)
- 压力测试 (并发和大文件)
- 兼容性测试 (多平台)

**性能基准要求**:
- FunASR 处理速度: RTF < 0.3 (中文)
- Whisper 处理速度: RTF < 0.5 (多语言)
- 内存使用: < 4GB (large 模型)
- 并发处理: 支持 4 个并行任务
- 启动时间: < 30 秒

**验收标准**:
- 所有性能指标达到要求
- 测试覆盖率 > 90%
- 内存泄漏检测通过
- 长时间运行稳定性测试通过
- 异常情况恢复正常
- 跨平台兼容性测试通过

**注意事项**:
- GPU 内存的动态管理
- 模型切换时的资源释放
- 异常情况的资源清理 