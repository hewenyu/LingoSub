# faster-whisper 引擎模块

基于 OpenAI Whisper 的高速多语言语音识别引擎，采用 CTranslate2 优化实现。

## 核心功能

- **多语言支持**：100+ 种语言识别
- **高速推理**：比原版 Whisper 快 4x
- **词级时间戳**：精确的词汇级时间对齐
- **自动语言检测**：智能识别音频语言
- **VAD 过滤**：语音活动检测去除静音

## 支持的模型

- `large-v3`：最高质量模型 (2.87B 参数)
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

## 使用示例

```python
from whisper_engine import WhisperEngine

engine = WhisperEngine({
    "model_size": "large-v3",
    "device": "cuda",
    "compute_type": "float16"
})

result = await engine.transcribe("audio.wav", {
    "language": "auto",  # 自动检测
    "word_timestamps": True,
    "vad_filter": True
})

print(f"语言: {result.language}")
print(f"文本: {result.text}")
for word in result.words:
    print(f"{word.word}: {word.start:.2f}s - {word.end:.2f}s")
``` 