# FunASR 引擎模块

基于阿里巴巴 FunASR 的中文优化语音识别引擎，专注于中文语音转录的准确性和效率。

## 核心功能

- **中文优化**：针对中文语音特点优化的识别算法
- **多模型支持**：Paraformer、SenseVoice 等先进模型
- **实时转录**：支持流式和批量处理模式
- **自动标点**：智能添加标点符号和语气词
- **热词定制**：支持专业术语和自定义词汇

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

## 使用示例

```python
from funasr_engine import FunASREngine

engine = FunASREngine({
    "model": "paraformer-zh",
    "device": "cuda",
    "batch_size": 1
})

result = await engine.transcribe("audio.wav")
print(result.text)  # 转录文本
print(result.timestamps)  # 时间戳
``` 