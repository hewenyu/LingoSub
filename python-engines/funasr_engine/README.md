# FunASR 引擎模块

基于阿里巴巴 FunASR 的中文优化语音识别引擎，专注于中文语音转录的准确性和效率。

## 核心功能

- **中文优化**：针对中文语音特点优化的识别算法
- **多模型支持**：Paraformer、SenseVoice 等先进模型
- **实时转录**：支持流式和批量处理模式
- **自动标点**：智能添加标点符号和语气词
- **热词定制**：支持专业术语和自定义词汇

## API 接口规范

### Sidecar 通信协议

```python
# 转录请求格式
@dataclass
class TranscribeRequest:
    audio_path: str
    language: Optional[str] = "zh"
    model_name: Optional[str] = "paraformer-zh"
    options: Dict[str, Any] = field(default_factory=dict)

# 转录响应格式
@dataclass  
class TranscribeResponse:
    segments: List[SubtitleSegment]
    metadata: TranscriptionMetadata
    processing_time: float

# 字幕段格式
@dataclass
class SubtitleSegment:
    start_time: float  # 秒
    end_time: float    # 秒
    text: str
    confidence: float
    words: Optional[List[WordTiming]] = None
    language: Optional[str] = "zh"
```

### 核心接口实现

```python
class FunASREngine(BaseSidecarEngine):
    async def transcribe(self, request: TranscribeRequest) -> TranscribeResponse:
        """转录音频文件"""
        pass
    
    async def health_check(self) -> HealthStatus:
        """健康检查"""
        pass
    
    async def get_capabilities(self) -> EngineCapabilities:
        """获取引擎能力"""
        pass
```

## 支持的模型

- `paraformer-zh`：中文通用识别模型
- `SenseVoiceSmall`：多语言轻量级模型
- `paraformer-zh-streaming`：实时流式识别
- 自定义模型路径支持

## 技术规格

- **准确率**：中文识别 WER < 5%
- **处理速度**：RTF < 0.5 (实时因子)
- **音频格式**：WAV, MP3, MP4, FLAC
- **采样率**：8kHz - 48kHz
- **语言支持**：中文(简体/繁体)、英文、日文

## JSON-RPC 通信示例

### 转录请求
```json
{
  "id": "req-001",
  "method": "transcribe",
  "params": {
    "audio_path": "/path/to/audio.wav",
    "language": "zh",
    "model_name": "paraformer-zh",
    "options": {
      "enable_vad": true,
      "enable_punc": true,
      "enable_itn": true
    }
  },
  "timeout": 30000
}
```

### 转录响应
```json
{
  "id": "req-001",
  "result": {
    "segments": [
      {
        "start_time": 0.0,
        "end_time": 2.5,
        "text": "欢迎使用LingoSub字幕生成工具。",
        "confidence": 0.95,
        "language": "zh"
      }
    ],
    "metadata": {
      "engine": "funasr",
      "model": "paraformer-zh",
      "language": "zh",
      "duration": 10.5
    },
    "processing_time": 2.1
  },
  "error": null
}
```

## 模块结构

```
funasr_engine/
├── engine.py          # 引擎核心实现
├── models.py          # 模型管理
├── processor.py       # 音频预处理
├── config.py          # 配置管理
├── __init__.py        # 模块初始化
└── tests/             # 单元测试
```

## 配置选项

```python
@dataclass
class FunASRConfig:
    model_name: str = "paraformer-zh"
    device: str = "cuda"
    batch_size: int = 1
    enable_vad: bool = True
    enable_punc: bool = True
    enable_itn: bool = True
    vad_model: Optional[str] = None
    punc_model: Optional[str] = None
    custom_vocab: Optional[List[str]] = None
```

## 错误处理

```python
class FunASRError(Exception):
    """FunASR 引擎错误基类"""
    pass

class ModelLoadError(FunASRError):
    """模型加载错误"""
    pass

class TranscriptionError(FunASRError):
    """转录处理错误"""
    pass
```

## 使用示例

```python
from funasr_engine import FunASREngine

# 初始化引擎
engine = FunASREngine({
    "model_name": "paraformer-zh",
    "device": "cuda",
    "batch_size": 1,
    "enable_vad": True
})

# 转录音频
request = TranscribeRequest(
    audio_path="audio.wav",
    language="zh",
    options={"enable_punc": True}
)

result = await engine.transcribe(request)
print(f"转录结果: {result.segments[0].text}")
print(f"处理时间: {result.processing_time:.2f}s")
``` 