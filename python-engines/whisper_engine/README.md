# faster-whisper 引擎模块

基于 OpenAI Whisper 的高速多语言语音识别引擎，采用 CTranslate2 优化实现，专为 Netflix 级别字幕输出设计。

## 核心功能

- **多语言支持**：100+ 种语言识别
- **高速推理**：比原版 Whisper 快 4x
- **词级时间戳**：精确的词汇级时间对齐
- **自动语言检测**：智能识别音频语言
- **VAD 过滤**：语音活动检测去除静音
- **Netflix 级别输出**：满足专业字幕制作标准

## API 接口规范

### Sidecar 通信协议

```python
# 转录请求格式
@dataclass
class TranscribeRequest:
    audio_path: str
    language: Optional[str] = "auto"
    model_name: Optional[str] = "large-v3"
    options: Dict[str, Any] = field(default_factory=dict)

# 转录响应格式
@dataclass  
class TranscribeResponse:
    segments: List[SubtitleSegment]
    metadata: TranscriptionMetadata
    processing_time: float

# 字幕段格式（支持词级时间戳）
@dataclass
class SubtitleSegment:
    start_time: float  # 秒
    end_time: float    # 秒
    text: str
    confidence: float
    words: Optional[List[WordTiming]] = None
    language: Optional[str] = None

@dataclass
class WordTiming:
    word: str
    start_time: float
    end_time: float
    confidence: float
```

### 核心接口实现

```python
class WhisperEngine(BaseSidecarEngine):
    async def transcribe(self, request: TranscribeRequest) -> TranscribeResponse:
        """转录音频文件，支持 Netflix 级别输出"""
        pass
    
    async def health_check(self) -> HealthStatus:
        """健康检查"""
        pass
    
    async def get_capabilities(self) -> EngineCapabilities:
        """获取引擎能力"""
        pass
```

## Netflix 级别配置

### 关键参数设置

```python
@dataclass
class WhisperConfig:
    model_size: str = "large-v3"
    device: str = "cuda"
    compute_type: str = "float16"
    
    # Netflix 级别参数
    beam_size: int = 5              # 提高转录准确性
    word_timestamps: bool = True    # 启用词级时间戳
    vad_filter: bool = True         # 过滤非语音部分
    
    # 高级参数
    temperature: List[float] = field(default_factory=lambda: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    compression_ratio_threshold: float = 2.4
    log_prob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    hallucination_silence_threshold: float = 2.0
    
    # VAD 参数
    vad_parameters: Dict[str, Any] = field(default_factory=lambda: {
        "min_silence_duration_ms": 500
    })
```

## 支持的模型

- `large-v3`：最高质量模型 (2.87B 参数) - **推荐用于 Netflix 级别**
- `large-v3-turbo`：高速优化版本
- `medium`：平衡质量与速度
- `small`：轻量级快速推理
- 自定义模型路径支持

## 技术规格

- **语言支持**：100+ 种语言
- **处理速度**：RTF < 0.3 (实时因子)
- **音频格式**：WAV, MP3, MP4, M4A, FLAC
- **采样率**：自动重采样至 16kHz
- **精度支持**：float32, float16, int8

## JSON-RPC 通信示例

### Netflix 级别转录请求
```json
{
  "id": "req-002",
  "method": "transcribe",
  "params": {
    "audio_path": "/path/to/video_audio.mp3",
    "language": "auto",
    "model_name": "large-v3",
    "options": {
      "beam_size": 5,
      "word_timestamps": true,
      "vad_filter": true,
      "temperature": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
      "hallucination_silence_threshold": 2.0,
      "vad_parameters": {
        "min_silence_duration_ms": 500
      }
    }
  },
  "timeout": 60000
}
```

### 转录响应（包含词级时间戳）
```json
{
  "id": "req-002",
  "result": {
    "segments": [
      {
        "start_time": 0.0,
        "end_time": 3.2,
        "text": "Welcome to LingoSub subtitle generation tool.",
        "confidence": 0.98,
        "language": "en",
        "words": [
          {"word": "Welcome", "start_time": 0.0, "end_time": 0.5, "confidence": 0.99},
          {"word": "to", "start_time": 0.5, "end_time": 0.7, "confidence": 0.98},
          {"word": "LingoSub", "start_time": 0.7, "end_time": 1.3, "confidence": 0.97}
        ]
      }
    ],
    "metadata": {
      "engine": "faster-whisper",
      "model": "large-v3",
      "language": "en",
      "duration": 15.8,
      "detected_language_probability": 0.99
    },
    "processing_time": 4.2
  },
  "error": null
}
```

## 批量处理支持

```python
from faster_whisper import BatchedInferencePipeline

class WhisperBatchEngine:
    def __init__(self, config: WhisperConfig):
        self.model = WhisperModel(
            config.model_size, 
            device=config.device, 
            compute_type=config.compute_type
        )
        self.batched_model = BatchedInferencePipeline(model=self.model)
    
    async def transcribe_batch(self, audio_files: List[str]) -> List[TranscribeResponse]:
        """批量处理多个音频文件"""
        pass
```

## 模块结构

```
whisper_engine/
├── engine.py          # 引擎核心实现
├── models.py          # 模型管理
├── transcriber.py     # 转录处理器
├── language.py        # 语言检测
├── config.py          # 配置管理
├── __init__.py        # 模块初始化
└── tests/             # 单元测试
```

## 错误处理

```python
class WhisperError(Exception):
    """Whisper 引擎错误基类"""
    pass

class ModelLoadError(WhisperError):
    """模型加载错误"""
    pass

class TranscriptionError(WhisperError):
    """转录处理错误"""
    pass

class LanguageDetectionError(WhisperError):
    """语言检测错误"""
    pass
```

## Netflix 级别使用示例

```python
from whisper_engine import WhisperEngine

# 初始化 Netflix 级别配置
engine = WhisperEngine({
    "model_size": "large-v3",
    "device": "cuda",
    "compute_type": "float16",
    "beam_size": 5,
    "word_timestamps": True,
    "vad_filter": True
})

# Netflix 级别转录
request = TranscribeRequest(
    audio_path="netflix_content.wav",
    language="auto",  # 自动检测
    options={
        "hallucination_silence_threshold": 2.0,
        "vad_parameters": {"min_silence_duration_ms": 500}
    }
)

result = await engine.transcribe(request)

# 输出 Netflix 格式字幕
for segment in result.segments:
    print(f"{segment.start_time:.2f} --> {segment.end_time:.2f}")
    print(segment.text)
    
    # 词级时间戳（用于精确编辑）
    if segment.words:
        for word in segment.words:
            print(f"  [{word.start_time:.2f}s-{word.end_time:.2f}s] {word.word}")
    print()

print(f"检测语言: {result.metadata.language}")
print(f"语言置信度: {result.metadata.detected_language_probability:.2f}")
print(f"处理时间: {result.processing_time:.2f}s")
```

## 性能优化

### GPU 内存优化
```python
# 对于大型模型，使用 float16 精度
config = WhisperConfig(
    model_size="large-v3",
    compute_type="float16",  # 节省 GPU 内存
    device="cuda"
)
```

### 批量处理优化
```python
# 使用批量推理提高处理效率
batched_engine = WhisperBatchEngine(config)
results = await batched_engine.transcribe_batch([
    "video1.mp3", 
    "video2.mp3", 
    "video3.mp3"
])
``` 