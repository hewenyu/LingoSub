[return to modelscope/FunASR](/modelscope/FunASR)

我需要输出netflix级别的字幕，如何实现

Deep

Searched across modelscope/FunASR

<button>Thought Process</button>

# 实现Netflix级别字幕的解决方案

要在FunASR中实现Netflix级别的字幕，您需要结合以下几个关键组件：

## 1\. 高质量语音识别模型

使用FunASR的顶级模型来确保转录准确性：

* **SenseVoice模型**：这是一个多语言语音基础模型，支持中文、英文、粤语、日语、韩语，并具备情感识别和音频事件检测功能 model.py:1-50

* **Paraformer系列**：非自回归端到端语音识别模型，提供高精度转录 model.py:1-50

* **Whisper-large-v3**：支持多语言高质量转录 model.py:1-50

## 2\. 精确时间戳生成

Netflix级别字幕需要精确的时间同步：

* **词级时间戳**：使用`ts_prediction_lfr6_standard()`函数生成精确的词级时间戳 timestamp\_tools.py:1-100

* **句级时间戳**：通过`timestamp_sentence()`和`timestamp_sentence_en()`函数生成句级时间戳 timestamp\_tools.py:100-200

## 3\. 实时字幕流

实现流式字幕服务：

* **WebSocket服务器**：提供实时字幕流服务 funasr\_wss\_server.py:1-50

* **实时协议**：支持在线、离线和2pass模式的字幕生成 websocket\_protocol\_zh.md:1-50

## 4\. 文本质量优化

提升字幕可读性和专业性：

* **标点符号恢复**：使用CT-Transformer模型添加标点符号 README\_zh.md:100-120

* **文本规范化**：通过ITN（逆文本规范化）处理数字、时间等特殊文本 README.md:1-30

* **后处理工具**：使用专门的后处理函数优化输出格式 postprocess\_utils.py:1-50

## 5\. 部署和性能优化

* **ONNX运行时**：提供高性能推理 timestamp\_utils.py:1-30

* **C++运行时**：提供更高性能的时间戳处理 util.cpp:1-100

## 实施建议

1. **选择合适的模型**：根据您的语言需求选择SenseVoice（多语言）或Paraformer（中文优化）
2. **配置时间戳精度**：启用词级和句级时间戳以获得最佳同步效果
3. **启用文本后处理**：确保标点符号和文本规范化功能开启
4. **使用WebSocket协议**：实现实时字幕流服务
5. **性能优化**：根据部署环境选择ONNX或C++运行时

## Notes

FunASR提供了完整的工具链来实现Netflix级别的字幕生成，包括高精度的语音识别模型、精确的时间戳生成、实时流式处理、以及专业的文本后处理功能。通过合理配置这些组件，您可以获得媲美商业级字幕服务的质量和性能。

<button>Copy Response</button><button>Share</button>

[modelscope/FunASR](https://github.com/modelscope/FunASR)[funasr/models/sense\_voice/model.py](https://github.com/modelscope/FunASR/blob/05c8eba1/funasr/models/sense_voice/model.py)

```
1from typing import Iterable, Optional
2import types
3import time
4import numpy as np
5import torch
6import torch.nn.functional as F
7from torch import Tensor
8from torch import nn
9from torch.cuda.amp import autocast
10from funasr.metrics.compute_acc import compute_accuracy, th_accuracy
11from funasr.losses.label_smoothing_loss import LabelSmoothingLoss
12from funasr.train_utils.device_funcs import force_gatherable
13
14from funasr.utils.load_utils import load_audio_text_image_video, extract_fbank
15from funasr.utils.datadir_writer import DatadirWriter
16from funasr.models.ctc.ctc import CTC
17
18from funasr.register import tables
19
20
21from funasr.models.paraformer.search import Hypothesis
22from .utils.ctc_alignment import ctc_forced_align
23
24
25class SinusoidalPositionEncoder(torch.nn.Module):
26    """ """
27
28    def __int__(self, d_model=80, dropout_rate=0.1):
29        pass
30
31    def encode(
32        self, positions: torch.Tensor = None, depth: int = None, dtype: torch.dtype = torch.float32
33    ):
34        batch_size = positions.size(0)
35        positions = positions.type(dtype)
36        device = positions.device
37        log_timescale_increment = torch.log(torch.tensor([10000], dtype=dtype, device=device)) / (
38            depth / 2 - 1
39        )
40        inv_timescales = torch.exp(
41            torch.arange(depth / 2, device=device).type(dtype) * (-log_timescale_increment)
42        )
43        inv_timescales = torch.reshape(inv_timescales, [batch_size, -1])
44        scaled_time = torch.reshape(positions, [1, -1, 1]) * torch.reshape(
45            inv_timescales, [1, 1, -1]
46        )
47        encoding = torch.cat([torch.sin(scaled_time), torch.cos(scaled_time)], dim=2)
48        return encoding.type(dtype)
49
50    def forward(self, x):
```

```
51        batch_size, timesteps, input_dim = x.size()
52        positions = torch.arange(1, timesteps + 1, device=x.device)[None, :]
53        position_encoding = self.encode(positions, input_dim, x.dtype).to(x.device)
```

[modelscope/FunASR](https://github.com/modelscope/FunASR)[funasr/models/paraformer/model.py](https://github.com/modelscope/FunASR/blob/05c8eba1/funasr/models/paraformer/model.py)

```
1#!/usr/bin/env python3
2# -*- encoding: utf-8 -*-
3# Copyright FunASR (https://github.com/alibaba-damo-academy/FunASR). All Rights Reserved.
4#  MIT License  (https://opensource.org/licenses/MIT)
5
6import time
7import copy
8import torch
9import logging
10from torch.cuda.amp import autocast
11from typing import Union, Dict, List, Tuple, Optional
12
13from funasr.register import tables
14from funasr.models.ctc.ctc import CTC
15from funasr.utils import postprocess_utils
16from funasr.metrics.compute_acc import th_accuracy
17from funasr.train_utils.device_funcs import to_device
18from funasr.utils.datadir_writer import DatadirWriter
19from funasr.models.paraformer.search import Hypothesis
20from funasr.models.paraformer.cif_predictor import mae_loss
21from funasr.train_utils.device_funcs import force_gatherable
22from funasr.losses.label_smoothing_loss import LabelSmoothingLoss
23from funasr.models.transformer.utils.add_sos_eos import add_sos_eos
24from funasr.models.transformer.utils.nets_utils import make_pad_mask
25from funasr.utils.timestamp_tools import ts_prediction_lfr6_standard
26from funasr.utils.load_utils import load_audio_text_image_video, extract_fbank
27
28
29@tables.register("model_classes", "Paraformer")
30class Paraformer(torch.nn.Module):
31    """
32    Author: Speech Lab of DAMO Academy, Alibaba Group
33    Paraformer: Fast and Accurate Parallel Transformer for Non-autoregressive End-to-End Speech Recognition
34    https://arxiv.org/abs/2206.08317
35    """
36
37    def __init__(
38        self,
39        specaug: Optional[str] = None,
40        specaug_conf: Optional[Dict] = None,
41        normalize: str = None,
42        normalize_conf: Optional[Dict] = None,
43        encoder: str = None,
44        encoder_conf: Optional[Dict] = None,
45        decoder: str = None,
46        decoder_conf: Optional[Dict] = None,
47        ctc: str = None,
48        ctc_conf: Optional[Dict] = None,
49        predictor: str = None,
50        predictor_conf: Optional[Dict] = None,
```

```
51        ctc_weight: float = 0.5,
52        input_size: int = 80,
53        vocab_size: int = -1,
```

[modelscope/FunASR](https://github.com/modelscope/FunASR)[funasr/models/whisper/model.py](https://github.com/modelscope/FunASR/blob/05c8eba1/funasr/models/whisper/model.py)

```
1from dataclasses import dataclass
2from typing import Dict
3from typing import Iterable, Optional
4import time
5import numpy as np
6import torch
7import torch.nn.functional as F
8from torch import Tensor
9from torch import nn
10
11import whisper
12
13# import whisper_timestamped as whisper
14
15from funasr.utils.load_utils import load_audio_text_image_video, extract_fbank
16
17from funasr.register import tables
18
19
20@tables.register("model_classes", "Whisper-tiny.en")
21@tables.register("model_classes", "Whisper-tiny")
22@tables.register("model_classes", "Whisper-base.en")
23@tables.register("model_classes", "Whisper-base")
24@tables.register("model_classes", "Whisper-small.en")
25@tables.register("model_classes", "Whisper-small")
26@tables.register("model_classes", "Whisper-medium.en")
27@tables.register("model_classes", "Whisper-medium")
28@tables.register("model_classes", "Whisper-large-v1")
29@tables.register("model_classes", "Whisper-large-v2")
30@tables.register("model_classes", "Whisper-large-v3")
31@tables.register("model_classes", "Whisper-large-v3-turbo")
32@tables.register("model_classes", "WhisperWarp")
33class WhisperWarp(nn.Module):
34    def __init__(self, *args, **kwargs):
35        super().__init__()
36        hub = kwargs.get("hub", "funasr")
37        if hub == "openai":
38            model_or_path = kwargs.get("model_path", "Whisper-large-v3")
39            if model_or_path.startswith("Whisper-"):
40                model_or_path = model_or_path.replace("Whisper-", "")
41            model = whisper.load_model(model_or_path)
42        else:
43            dims = kwargs.get("dims", {})
44            dims = whisper.model.ModelDimensions(**dims)
45            model = whisper.model.Whisper(dims=dims)
46
47        self.model = model
48
49        self.encoder_output_size = self.model.dims.n_audio_state
50
```

```
51    def forward(
52        self,
53    ):
```

[modelscope/FunASR](https://github.com/modelscope/FunASR)[funasr/utils/timestamp\_tools.py](https://github.com/modelscope/FunASR/blob/05c8eba1/funasr/utils/timestamp_tools.py)

```
1import torch
2import codecs
3import logging
4import argparse
5import numpy as np
6
7# import edit_distance
8from itertools import zip_longest
9
10
11def cif_wo_hidden(alphas, threshold):
12    batch_size, len_time = alphas.size()
13    # loop varss
14    integrate = torch.zeros([batch_size], device=alphas.device)
15    # intermediate vars along time
16    list_fires = []
17    for t in range(len_time):
18        alpha = alphas[:, t]
19        integrate += alpha
20        list_fires.append(integrate)
21        fire_place = integrate >= threshold
22        integrate = torch.where(
23            fire_place,
24            integrate - torch.ones([batch_size], device=alphas.device) * threshold,
25            integrate,
26        )
27    fires = torch.stack(list_fires, 1)
28    return fires
29
30
31def ts_prediction_lfr6_standard(
32    us_alphas, us_peaks, char_list, vad_offset=0.0, force_time_shift=-1.5, sil_in_str=True, upsample_rate=3,
33):
34    if not len(char_list):
35        return "", []
36    START_END_THRESHOLD = 5
37    MAX_TOKEN_DURATION = 12  #  3 times upsampled
38    TIME_RATE=10.0 * 6 / 1000 / upsample_rate
39    if len(us_alphas.shape) == 2:
40        alphas, peaks = us_alphas[0], us_peaks[0]  # support inference batch_size=1 only
41    else:
42        alphas, peaks = us_alphas, us_peaks
43    if char_list[-1] == "</s>":
44        char_list = char_list[:-1]
45    fire_place = (
46        torch.where(peaks >= 1.0 - 1e-4)[0].cpu().numpy() + force_time_shift
47    )  # total offset
48    if len(fire_place) != len(char_list) + 1:
49        alphas /= alphas.sum() / (len(char_list) + 1)
50        alphas = alphas.unsqueeze(0)
51        peaks = cif_wo_hidden(alphas, threshold=1.0 - 1e-4)[0]
52        fire_place = (
53            torch.where(peaks >= 1.0 - 1e-4)[0].cpu().numpy() + force_time_shift
54        )  # total offset
55    num_frames = peaks.shape[0]
56    timestamp_list = []
57    new_char_list = []
58    # for bicif model trained with large data, cif2 actually fires when a character starts
59    # so treat the frames between two peaks as the duration of the former token
60    # fire_place = torch.where(peaks>=1.0-1e-4)[0].cpu().numpy() + force_time_shift  # total offset
61    # assert num_peak == len(char_list) + 1 # number of peaks is supposed to be number of tokens + 1
62    # begin silence
63    if fire_place[0] > START_END_THRESHOLD:
64        # char_list.insert(0, '<sil>')
65        timestamp_list.append([0.0, fire_place[0] * TIME_RATE])
66        new_char_list.append("<sil>")
67    # tokens timestamp
68    for i in range(len(fire_place) - 1):
69        new_char_list.append(char_list[i])
70        if MAX_TOKEN_DURATION < 0 or fire_place[i + 1] - fire_place[i] <= MAX_TOKEN_DURATION:
71            timestamp_list.append([fire_place[i] * TIME_RATE, fire_place[i + 1] * TIME_RATE])
72        else:
73            # cut the duration to token and sil of the 0-weight frames last long
74            _split = fire_place[i] + MAX_TOKEN_DURATION
75            timestamp_list.append([fire_place[i] * TIME_RATE, _split * TIME_RATE])
76            timestamp_list.append([_split * TIME_RATE, fire_place[i + 1] * TIME_RATE])
77            new_char_list.append("<sil>")
78    # tail token and end silence
79    # new_char_list.append(char_list[-1])
80    if num_frames - fire_place[-1] > START_END_THRESHOLD:
81        _end = (num_frames + fire_place[-1]) * 0.5
82        # _end = fire_place[-1]
83        timestamp_list[-1][1] = _end * TIME_RATE
84        timestamp_list.append([_end * TIME_RATE, num_frames * TIME_RATE])
85        new_char_list.append("<sil>")
86    else:
87        if len(timestamp_list)>0:
88            timestamp_list[-1][1] = num_frames * TIME_RATE
89    if vad_offset:  # add offset time in model with vad
90        for i in range(len(timestamp_list)):
91            timestamp_list[i][0] = timestamp_list[i][0] + vad_offset / 1000.0
92            timestamp_list[i][1] = timestamp_list[i][1] + vad_offset / 1000.0
93    res_txt = ""
94    for char, timestamp in zip(new_char_list, timestamp_list):
95        # if char != '<sil>':
96        if not sil_in_str and char == "<sil>":
97            continue
98        res_txt += "{} {} {};".format(
99            char, str(timestamp[0] + 0.0005)[:5], str(timestamp[1] + 0.0005)[:5]
100        )
101    res = []
102    for char, timestamp in zip(new_char_list, timestamp_list):
103        if char != "<sil>":
104            res.append([int(timestamp[0] * 1000), int(timestamp[1] * 1000)])
105    return res_txt, res
106
107
108def timestamp_sentence(
109    punc_id_list, timestamp_postprocessed, text_postprocessed, return_raw_text=False
110):
111    punc_list = ["，", "。", "？", "、"]
112    res = []
113    if text_postprocessed is None:
114        return res
115    if timestamp_postprocessed is None:
116        return res
117    if len(timestamp_postprocessed) == 0:
118        return res
119    if len(text_postprocessed) == 0:
120        return res
121
122    if punc_id_list is None or len(punc_id_list) == 0:
123        res.append(
124            {
125                "text": text_postprocessed.split(),
126                "start": timestamp_postprocessed[0][0],
127                "end": timestamp_postprocessed[-1][1],
128                "timestamp": timestamp_postprocessed,
129            }
130        )
131        return res
132    if len(punc_id_list) != len(timestamp_postprocessed):
133        logging.warning("length mismatch between punc and timestamp")
134    sentence_text = ""
135    sentence_text_seg = ""
136    ts_list = []
137    sentence_start = timestamp_postprocessed[0][0]
138    sentence_end = timestamp_postprocessed[0][1]
139    texts = text_postprocessed.split()
140    punc_stamp_text_list = list(
141        zip_longest(punc_id_list, timestamp_postprocessed, texts, fillvalue=None)
142    )
143    for punc_stamp_text in punc_stamp_text_list:
144        punc_id, timestamp, text = punc_stamp_text
145        if sentence_start is None and timestamp is not None:
146            sentence_start = timestamp[0]
147        # sentence_text += text if text is not None else ''
148        if text is not None:
149            if "a" <= text[0] <= "z" or "A" <= text[0] <= "Z":
150                sentence_text += " " + text
151            elif len(sentence_text) and (
152                "a" <= sentence_text[-1] <= "z" or "A" <= sentence_text[-1] <= "Z"
153            ):
154                sentence_text += " " + text
155            else:
156                sentence_text += text
157            sentence_text_seg += text + " "
158        ts_list.append(timestamp)
159
160        punc_id = int(punc_id) if punc_id is not None else 1
161        sentence_end = timestamp[1] if timestamp is not None else sentence_end
162        sentence_text_seg = (
163            sentence_text_seg[:-1] if sentence_text_seg and sentence_text_seg[-1] == " " else sentence_text_seg
164        )
165        if punc_id > 1:
166            sentence_text += punc_list[punc_id - 2]
167            if return_raw_text:
168                res.append(
169                    {
170                        "text": sentence_text,
171                        "start": sentence_start,
172                        "end": sentence_end,
173                        "timestamp": ts_list,
174                        "raw_text": sentence_text_seg,
175                    }
176                )
177            else:
178                res.append(
179                    {
180                        "text": sentence_text,
181                        "start": sentence_start,
182                        "end": sentence_end,
183                        "timestamp": ts_list,
184                    }
185                )
186            sentence_text = ""
187            sentence_text_seg = ""
188            ts_list = []
189            sentence_start = None
190    return res
191
192
193def timestamp_sentence_en(
194    punc_id_list, timestamp_postprocessed, text_postprocessed, return_raw_text=False
195):
196    punc_list = [",", ".", "?", ","]
197    res = []
198    if text_postprocessed is None:
199        return res
200    if timestamp_postprocessed is None:
```

```
201        return res
202    if len(timestamp_postprocessed) == 0:
203        return res
```

[modelscope/FunASR](https://github.com/modelscope/FunASR)[runtime/python/websocket/funasr\_wss\_server.py](https://github.com/modelscope/FunASR/blob/05c8eba1/runtime/python/websocket/funasr_wss_server.py)

```
1import asyncio
2import json
3import websockets
4import time
5import logging
6import tracemalloc
7import numpy as np
8import argparse
9import ssl
10
11
12parser = argparse.ArgumentParser()
13parser.add_argument(
14    "--host", type=str, default="0.0.0.0", required=False, help="host ip, localhost, 0.0.0.0"
15)
16parser.add_argument("--port", type=int, default=10095, required=False, help="grpc server port")
17parser.add_argument(
18    "--asr_model",
19    type=str,
20    default="iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
21    help="model from modelscope",
22)
23parser.add_argument("--asr_model_revision", type=str, default="v2.0.4", help="")
24parser.add_argument(
25    "--asr_model_online",
26    type=str,
27    default="iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online",
28    help="model from modelscope",
29)
30parser.add_argument("--asr_model_online_revision", type=str, default="v2.0.4", help="")
31parser.add_argument(
32    "--vad_model",
33    type=str,
34    default="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
35    help="model from modelscope",
36)
37parser.add_argument("--vad_model_revision", type=str, default="v2.0.4", help="")
38parser.add_argument(
39    "--punc_model",
40    type=str,
41    default="iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727",
42    help="model from modelscope",
43)
44parser.add_argument("--punc_model_revision", type=str, default="v2.0.4", help="")
45parser.add_argument("--ngpu", type=int, default=1, help="0 for cpu, 1 for gpu")
46parser.add_argument("--device", type=str, default="cuda", help="cuda, cpu")
47parser.add_argument("--ncpu", type=int, default=4, help="cpu cores")
48parser.add_argument(
49    "--certfile",
50    type=str,
```

```
51    default="../../ssl_key/server.crt",
52    required=False,
53    help="certfile for ssl",
```

[modelscope/FunASR](https://github.com/modelscope/FunASR)[runtime/docs/websocket\_protocol\_zh.md](https://github.com/modelscope/FunASR/blob/05c8eba1/runtime/docs/websocket_protocol_zh.md)

    1(简体中文|[English](./websocket_protocol.md))
    2# websocket/grpc通信协议
    3
    4本协议为FunASR软件包通信协议，分为离线文件转写（[部署文档](./SDK_tutorial_zh.md)），实时语音识别（[部署文档](./SDK_tutorial_online_zh.md)）
    5
    6## 离线文件转写
    7### 从客户端往服务端发送数据
    8#### 消息格式
    9配置参数与meta信息用json，音频数据采用bytes
    10#### 首次通信
    11message为（需要用json序列化）：
    12```text
    13{"mode": "offline", "wav_name": "wav_name", "wav_format":"pcm", "is_speaking": True, "hotwords":"{"阿里巴巴":20,"通义实验室":30}", "itn":True}
    14```
    15参数介绍：
    16```text
    17`mode`：`offline`，表示推理模式为离线文件转写
    18`wav_name`：表示需要推理音频文件名
    19`wav_format`：表示音视频文件后缀名，可选pcm、mp3、mp4等
    20`is_speaking`：False 表示断句尾点，例如，vad切割点，或者一条wav结束
    21`audio_fs`：当输入音频为pcm数据时，需要加上音频采样率参数
    22`hotwords`：如果使用热词，需要向服务端发送热词数据（字符串），格式为 "{"阿里巴巴":20,"通义实验室":30}"
    23`itn`: 设置是否使用itn，默认True
    24`svs_lang`: 设置SenseVoiceSmall模型语种，默认为“auto”
    25`svs_itn`: 设置SenseVoiceSmall模型是否开启标点、ITN，默认为True
    26```
    27注：热词权重仅在fst热词服务下生效。
    28
    29#### 发送音频数据
    30pcm直接将音频数据，其他格式音频数据，连同头部信息与音视频bytes数据发送，支持多种采样率与音视频格式
    31
    32#### 发送音频结束标志
    33音频数据发送结束后，需要发送结束标志（需要用json序列化）：
    34```text
    35{"is_speaking": False}
    36```
    37
    38### 从服务端往客户端发数据
    39#### 发送识别结果
    40message为（采用json序列化）
    41```text
    42{"mode": "offline", "wav_name": "wav_name", "text": "asr ouputs", "is_final": True,"timestamp":"[[100,200], [200,500]]","stamp_sents":[]}
    43```
    44参数介绍：
    45```text
    46`mode`：`offline`，表示推理模式为离线文件转写
    47`wav_name`：表示需要推理音频文件名
    48`text`：表示语音识别输出文本
    49`is_final`：表示识别结束，在 offline 模式下这个字段永远为 False，服务端 websocket 只会返回一次识别结果
    50`timestamp`：如果AM为时间戳模型，会返回此字段，表示时间戳，格式为 "[[100,200], [200,500]]"(ms)

    51`stamp_sents`：如果AM为时间戳模型，会返回此字段，表示句子级别时间戳，格式为 [{"text_seg":"正 是 因 为","punc":",","start":430,"end":1130,"ts_list":[[430,670],[670,810],[810,1030],[1030,1130]]}]
    52```
    53

[modelscope/FunASR](https://github.com/modelscope/FunASR)[README\_zh.md](https://github.com/modelscope/FunASR/blob/05c8eba1/README_zh.md)

```
97
98## 模型仓库
99
```

```
100FunASR开源了大量在工业数据上预训练模型，您可以在[模型许可协议](./MODEL_LICENSE)下自由使用、复制、修改和分享FunASR模型，下面列举代表性的模型，更多模型请参考 [模型仓库](./model_zoo)。
101
102（注：⭐ 表示ModelScope模型仓库，🤗 表示Huggingface模型仓库，🍀表示OpenAI模型仓库）
103
104
105|                                                                                                     模型名字                                                                                                      |        任务详情        |      训练数据      |  参数量   | 
106|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|:------------------:|:--------------:|:------:|
107|                                  SenseVoiceSmall <br> ([⭐](https://www.modelscope.cn/models/iic/SenseVoiceSmall)  [🤗](https://huggingface.co/FunAudioLLM/SenseVoiceSmall) )                                  |  多种语音理解能力，涵盖了自动语音识别（ASR）、语言识别（LID）、情感识别（SER）以及音频事件检测（AED）   |  400000小时，中文   |  330M  |
108|    paraformer-zh <br> ([⭐](https://www.modelscope.cn/models/damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch/summary)  [🤗](https://huggingface.co/funasr/paraformer-zh) )    |  语音识别，带时间戳输出，非实时   |   60000小时，中文   |  220M  |
109| paraformer-zh-streaming <br> ( [⭐](https://modelscope.cn/models/damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online/summary) [🤗](https://huggingface.co/funasr/paraformer-zh-streaming) ) |      语音识别，实时       |   60000小时，中文   |  220M  |
110|         paraformer-en <br> ( [⭐](https://www.modelscope.cn/models/damo/speech_paraformer-large-vad-punc_asr_nat-en-16k-common-vocab10020/summary) [🤗](https://huggingface.co/funasr/paraformer-en) )         |      语音识别，非实时      |   50000小时，英文   |  220M  |
111|                      conformer-en <br> ( [⭐](https://modelscope.cn/models/damo/speech_conformer_asr-en-16k-vocab4199-pytorch/summary) [🤗](https://huggingface.co/funasr/conformer-en) )                      |      语音识别，非实时      |   50000小时，英文   |  220M  |
112|                        ct-punc <br> ( [⭐](https://modelscope.cn/models/damo/punc_ct-transformer_cn-en-common-vocab471067-large/summary) [🤗](https://huggingface.co/funasr/ct-punc) )                         |        标点恢复        |   100M，中文与英文   |  290M  | 
113|                            fsmn-vad <br> ( [⭐](https://modelscope.cn/models/damo/speech_fsmn_vad_zh-cn-16k-common-pytorch/summary) [🤗](https://huggingface.co/funasr/fsmn-vad) )                             |     语音端点检测，实时      |  5000小时，中文与英文  |  0.4M  | 
114|                                                       fsmn-kws <br> ( [⭐](https://modelscope.cn/models/iic/speech_charctc_kws_phone-xiaoyun/summary) )                                                        |     语音唤醒，实时      |  5000小时，中文  |  0.7M  | 
115|                              fa-zh <br> ( [⭐](https://modelscope.cn/models/damo/speech_timestamp_prediction-v1-16k-offline/summary) [🤗](https://huggingface.co/funasr/fa-zh) )                               |      字级别时间戳预测      |   50000小时，中文   |  38M   |
116|                                 cam++ <br> ( [⭐](https://modelscope.cn/models/iic/speech_campplus_sv_zh-cn_16k-common/summary) [🤗](https://huggingface.co/funasr/campplus) )                                 |      说话人确认/分割      |     5000小时     |  7.2M  | 
117|                                     Whisper-large-v3 <br> ([⭐](https://www.modelscope.cn/models/iic/Whisper-large-v3/summary)  [🍀](https://github.com/openai/whisper) )                                      |  语音识别，带时间戳输出，非实时   |      多语言       | 1550 M |
118|                               Whisper-large-v3-turbo <br> ([⭐](https://www.modelscope.cn/models/iic/Whisper-large-v3-turbo/summary)  [🍀](https://github.com/openai/whisper) )                                |  语音识别，带时间戳输出，非实时   |      多语言       | 809 M |
119|                                         Qwen-Audio <br> ([⭐](examples/industrial_data_pretraining/qwen_audio/demo.py)  [🤗](https://huggingface.co/Qwen/Qwen-Audio) )                                         |  音频文本多模态大模型（预训练）   |      多语言       |   8B   |
120|                                 Qwen-Audio-Chat <br> ([⭐](examples/industrial_data_pretraining/qwen_audio/demo_chat.py)  [🤗](https://huggingface.co/Qwen/Qwen-Audio-Chat) )                                  | 音频文本多模态大模型（chat版本） |      多语言       |   8B   |
```

```
121|                        emotion2vec+large <br> ([⭐](https://modelscope.cn/models/iic/emotion2vec_plus_large/summary)  [🤗](https://huggingface.co/emotion2vec/emotion2vec_plus_large) )                        |    情感识别模型          | 40000小时，4种情感类别 |  300M  |
122
123<a name="快速开始"></a>
```

[modelscope/FunASR](https://github.com/modelscope/FunASR)[fun\_text\_processing/text\_normalization/zh/README.md](https://github.com/modelscope/FunASR/blob/05c8eba1/fun_text_processing/text_normalization/zh/README.md)

    1# Chinese Text Normalization
    2
    3## 1. How To Use
    4```
    5python normalize.py --language "zh" --text "text to be normalized"
    6```
    7
    8## 2. TN Pipeline
    9There are 3 components in TN pipeline:
    10* pre-processing (before tagger)
    11* non-standard word normalization
    12* post-processing (after verbalizer)
    13
    14### 2.1 Pre-Processing
    15#### Char Width Conversion (全角 -> 半角)
    16```
    17苹果ＣＥＯ宣布发布新ＩＰＨＯＮＥ -> 苹果CEO宣布发布新IPHONE
    18他说：“我们已经吃过了！”。 -> 他说:"我们已经吃过了!".
    19```
    20* covers English letters, digits, punctuations and some symbols
    21* the complete mapping table `data/char/fullwidth_to_halfwidth.tsv`
    22
    23#### Denylist (Removal)
    24Sometime you may want to remove certain things like interjections/fillers "啊", "呃" etc
    25```
    26呃这个呃啊我不知道 -> 这个我不知道
    27```
    28* customizable via `data/denylist/denylist.tsv`
    29
    30

    31### 2.2 Non-Standard-Words(NSW) normalization
    32#### Numbers
    33```

[modelscope/FunASR](https://github.com/modelscope/FunASR)[funasr/utils/postprocess\_utils.py](https://github.com/modelscope/FunASR/blob/05c8eba1/funasr/utils/postprocess_utils.py)

```
1# Copyright (c) Alibaba, Inc. and its affiliates.
2
3import string
4import logging
5from typing import Any, List, Union
6
7
8def isChinese(ch: str):
9    if "\u4e00" <= ch <= "\u9fff" or "\u0030" <= ch <= "\u0039" or ch == "@":
10        return True
11    return False
12
13
14def isAllChinese(word: Union[List[Any], str]):
15    word_lists = []
16    for i in word:
17        cur = i.replace(" ", "")
18        cur = cur.replace("</s>", "")
19        cur = cur.replace("<s>", "")
20        cur = cur.replace("<unk>", "")
21        cur = cur.replace("<OOV>", "")
22        word_lists.append(cur)
23
24    if len(word_lists) == 0:
25        return False
26
27    for ch in word_lists:
28        if isChinese(ch) is False:
29            return False
30    return True
31
32
33def isAllAlpha(word: Union[List[Any], str]):
34    word_lists = []
35    for i in word:
36        cur = i.replace(" ", "")
37        cur = cur.replace("</s>", "")
38        cur = cur.replace("<s>", "")
39        cur = cur.replace("<unk>", "")
40        cur = cur.replace("<OOV>", "")
41        word_lists.append(cur)
42
43    if len(word_lists) == 0:
44        return False
45
46    for ch in word_lists:
47        if ch.isalpha() is False and ch != "'":
48            return False
49        elif ch.isalpha() is True and isChinese(ch) is True:
50            return False
```

```
51
52    return True
53
```

[modelscope/FunASR](https://github.com/modelscope/FunASR)[runtime/python/onnxruntime/funasr\_onnx/utils/timestamp\_utils.py](https://github.com/modelscope/FunASR/blob/05c8eba1/runtime/python/onnxruntime/funasr_onnx/utils/timestamp_utils.py)

```
1# -*- encoding: utf-8 -*-
2# Copyright FunASR (https://github.com/alibaba-damo-academy/FunASR). All Rights Reserved.
3#  MIT License  (https://opensource.org/licenses/MIT)
4
5import numpy as np
6
7
8def time_stamp_lfr6_onnx(us_cif_peak, char_list, begin_time=0.0, total_offset=-1.5):
9    if not len(char_list):
10        return "", []
11    START_END_THRESHOLD = 5
12    MAX_TOKEN_DURATION = 30
13    TIME_RATE = 10.0 * 6 / 1000 / 3  #  3 times upsampled
14    cif_peak = us_cif_peak.reshape(-1)
15    num_frames = cif_peak.shape[-1]
16    if char_list[-1] == "</s>":
17        char_list = char_list[:-1]
18    # char_list = [i for i in text]
19    timestamp_list = []
20    new_char_list = []
21    # for bicif model trained with large data, cif2 actually fires when a character starts
22    # so treat the frames between two peaks as the duration of the former token
23    fire_place = np.where(cif_peak > 1.0 - 1e-4)[0] + total_offset  # np format
24    num_peak = len(fire_place)
25    assert num_peak == len(char_list) + 1  # number of peaks is supposed to be number of tokens + 1
26    # begin silence
27    if fire_place[0] > START_END_THRESHOLD:
28        # char_list.insert(0, '<sil>')
29        timestamp_list.append([0.0, fire_place[0] * TIME_RATE])
30        new_char_list.append("<sil>")
```

```
31    # tokens timestamp
32    for i in range(len(fire_place) - 1):
33        new_char_list.append(char_list[i])
```

[modelscope/FunASR](https://github.com/modelscope/FunASR)[runtime/onnxruntime/src/util.cpp](https://github.com/modelscope/FunASR/blob/05c8eba1/runtime/onnxruntime/src/util.cpp)

```
1
2#include "precomp.h"
3
4namespace funasr {
5float *LoadParams(const char *filename)
6{
7
8    FILE *fp;
9    fp = fopen(filename, "rb");
10    fseek(fp, 0, SEEK_END);
11    uint32_t nFileLen = ftell(fp);
12    fseek(fp, 0, SEEK_SET);
13
14    float *params_addr = (float *)AlignedMalloc(32, nFileLen);
15    int n = fread(params_addr, 1, nFileLen, fp);
16    fclose(fp);
17
18    return params_addr;
19}
20
21int ValAlign(int val, int align)
22{
23    float tmp = ceil((float)val / (float)align) * (float)align;
24    return (int)tmp;
25}
26
27void DispParams(float *din, int size)
28{
29    int i;
30    for (i = 0; i < size; i++) {
31        printf("%f ", din[i]);
32    }
33    printf("\n");
34}
35void SaveDataFile(const char *filename, void *data, uint32_t len)
36{
37    FILE *fp;
38    fp = fopen(filename, "wb+");
39    fwrite(data, 1, len, fp);
40    fclose(fp);
41}
42
43void BasicNorm(Tensor<float> *&din, float norm)
44{
45
46    int Tmax = din->size[2];
47
48    int i, j;
49    for (i = 0; i < Tmax; i++) {
50        float sum = 0;
51        for (j = 0; j < 512; j++) {
52            int ii = i * 512 + j;
53            sum += din->buff[ii] * din->buff[ii];
54        }
55        float mean = sqrt(sum / 512 + norm);
56        for (j = 0; j < 512; j++) {
57            int ii = i * 512 + j;
58            din->buff[ii] = din->buff[ii] / mean;
59        }
60    }
61}
62
63void FindMax(float *din, int len, float &max_val, int &max_idx)
64{
65    int i;
66    max_val = -INFINITY;
67    max_idx = -1;
68    for (i = 0; i < len; i++) {
69        if (din[i] > max_val) {
70            max_val = din[i];
71            max_idx = i;
72        }
73    }
74}
75
76string PathAppend(const string &p1, const string &p2)
77{
78
79    char sep = '/';
80    string tmp = p1;
81
82#ifdef _WIN32
83    sep = '\\';
84#endif
85
86    if (p1[p1.length()-1] != sep) { // Need to add a
87        tmp += sep;               // path separator
88        return (tmp + p2);
89    } else
90        return (p1 + p2);
91}
92
93void Relu(Tensor<float> *din)
94{
95    int i;
96    for (i = 0; i < din->buff_size; i++) {
97        float val = din->buff[i];
98        din->buff[i] = val < 0 ? 0 : val;
99    }
100}
```

```
101
102void Swish(Tensor<float> *din)
103{
```