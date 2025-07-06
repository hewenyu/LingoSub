# LingoSub Python Sidecar 基础架构

## 概述

LingoSub Python Sidecar 基础架构是一个完整的进程间通信和生命周期管理系统，专门为 ASR (自动语音识别) 引擎设计。它提供了统一的接口、稳定的通信机制和强大的监控功能。

## 架构特点

### 🚀 核心特性

- **统一引擎接口**: 所有 ASR 引擎继承同一个基类，确保接口一致性
- **进程间通信**: 基于 stdin/stdout 的 JSON-RPC 协议，稳定可靠
- **生命周期管理**: 完整的启动、停止、重启和健康检查机制
- **性能监控**: 实时系统资源监控和性能指标收集
- **配置管理**: 支持多种配置源的灵活配置系统
- **结构化日志**: 标准化的日志格式，便于分析和调试

### 🏗️ 架构组件

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tauri 后端    │◄──►│ SidecarCommunic │◄──►│  BaseSidecarEng │
│                 │    │     ator        │    │      ine        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ProcessMgr    │    │   ConfigMgr     │    │   SidecarLogger │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 快速开始

### 1. 创建自定义引擎

```python
# my_engine.py
from common.base_engine import BaseSidecarEngine
from common.models import TranscriptionRequest, TranscriptionResponse, EngineConfig
from common.config import SidecarConfig

class MyCustomEngine(BaseSidecarEngine):
    """自定义 ASR 引擎"""
    
    def _initialize_engine(self) -> None:
        """初始化引擎特定资源"""
        self.model = load_my_model()  # 加载你的模型
        
    async def _start_engine(self) -> None:
        """启动引擎"""
        # 执行启动逻辑
        pass
    
    async def _stop_engine(self) -> None:
        """停止引擎"""
        # 执行清理逻辑
        pass
    
    async def _check_engine_health(self) -> bool:
        """健康检查"""
        return self.model is not None
    
    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
        """执行转录"""
        # 实现你的转录逻辑
        result = await self.model.process(request.file_path)
        
        return TranscriptionResponse(
            task_id=request.task_id,
            status=TaskStatus.COMPLETED,
            text=result.text,
            timestamps=result.timestamps,
            confidence=result.confidence
        )

def create_engine(config: SidecarConfig) -> MyCustomEngine:
    """引擎工厂函数"""
    engine_config = EngineConfig(
        engine_id=config.engine_id,
        engine_type=EngineType.CUSTOM,
        model_name=config.model_name,
        device=config.device,
        language=config.language
    )
    return MyCustomEngine(engine_config)
```

### 2. 启动 Sidecar 进程

```python
# main.py
from common.lifecycle import run_sidecar
from my_engine import create_engine

if __name__ == "__main__":
    # 使用默认配置启动
    run_sidecar(create_engine)
    
    # 或者指定配置文件
    run_sidecar(create_engine, config_file="config.yaml")
```

### 3. 配置文件示例

```yaml
# config.yaml
engine_id: "my-engine-001"
engine_type: "custom"
model_name: "my-model-v1"
device: "cpu"
language: "zh"

performance:
  max_workers: 4
  timeout: 300
  memory_limit: 2048
  batch_size: 1

logging:
  level: "INFO"
  file_path: "logs/sidecar.log"
  console_output: true

security:
  enable_auth: false
  rate_limit: 100
```

## API 参考

### BaseSidecarEngine

所有引擎的基类，提供标准接口。

#### 必须实现的方法

```python
def _initialize_engine(self) -> None:
    """初始化引擎特定配置"""
    
async def _start_engine(self) -> None:
    """启动引擎"""
    
async def _stop_engine(self) -> None:
    """停止引擎"""
    
async def _check_engine_health(self) -> bool:
    """健康检查"""
    
async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
    """执行转录"""
```

#### 可用的方法

```python
async def start(self) -> None:
    """启动引擎（外部调用）"""
    
async def stop(self) -> None:
    """停止引擎（外部调用）"""
    
async def health_check(self) -> HealthStatus:
    """获取健康状态"""
    
async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理通用请求"""
    
def get_info(self) -> Dict[str, Any]:
    """获取引擎信息"""
```

### SidecarCommunicator

处理进程间通信的核心组件。

```python
class SidecarCommunicator:
    def __init__(self, command_handler: Callable):
        """初始化通信器"""
        
    async def start(self):
        """启动通信循环"""
        
    async def send_notification(self, notification_type: str, data: Dict[str, Any]):
        """发送通知"""
        
    async def send_heartbeat(self, engine_id: str, status: str):
        """发送心跳"""
```

### ProcessManager

管理进程生命周期。

```python
class ProcessManager:
    async def start(self) -> bool:
        """启动进程"""
        
    async def stop(self) -> bool:
        """停止进程"""
        
    async def restart(self) -> bool:
        """重启进程"""
        
    def get_status(self) -> Dict[str, Any]:
        """获取进程状态"""
```

## 通信协议

### 命令格式

```json
{
  "id": "unique-command-id",
  "type": "command-type",
  "payload": {
    "parameter1": "value1",
    "parameter2": "value2"
  },
  "timeout": 300,
  "created_at": "2024-12-19T10:30:00Z"
}
```

### 响应格式

成功响应：
```json
{
  "id": "command-id",
  "status": "success",
  "data": {
    "result": "response-data"
  },
  "timestamp": "2024-12-19T10:30:01Z"
}
```

错误响应：
```json
{
  "id": "command-id",
  "status": "error",
  "error": "Error message",
  "error_type": "ValueError",
  "timestamp": "2024-12-19T10:30:01Z"
}
```

### 支持的命令类型

| 命令类型 | 描述 | 参数 |
|---------|------|------|
| `transcribe` | 执行转录 | `TranscriptionRequest` |
| `health_check` | 健康检查 | 无 |
| `get_metrics` | 获取指标 | 无 |
| `get_status` | 获取状态 | 无 |
| `restart` | 重启进程 | 无 |
| `stop` | 停止进程 | 无 |

## 配置系统

### 配置优先级

1. 环境变量 (最高优先级)
2. 配置文件 (JSON/YAML)
3. 默认值 (最低优先级)

### 环境变量

所有配置都可以通过环境变量覆盖，前缀为 `LINGOSUB_`：

```bash
export LINGOSUB_ENGINE_ID="prod-engine-001"
export LINGOSUB_DEVICE="cuda"
export LINGOSUB_LOGGING='{"level": "DEBUG", "file_path": "/var/log/sidecar.log"}'
```

### 配置验证

```python
from common.config import ConfigManager

manager = ConfigManager()
if manager.validate():
    config = manager.load()
else:
    print("配置验证失败")
```

## 监控和日志

### 性能监控

```python
# 自动性能监控
engine.logger.performance_monitor.start_monitoring()

# 手动记录指标
engine.logger.log_metric("processing_time", 1.5)
engine.logger.log_performance("transcription", duration)

# 获取系统指标
metrics = engine.logger.performance_monitor.get_metrics()
```

### 结构化日志

```python
# 记录请求
engine.logger.log_request(request_id, "transcribe", params)

# 记录响应
engine.logger.log_response(request_id, "success", processing_time)

# 记录错误
engine.logger.log_error(exception, context)
```

### 日志格式

```json
{
  "timestamp": "2024-12-19T10:30:00.123Z",
  "level": "INFO",
  "logger": "sidecar.engine-001",
  "message": "Request completed successfully",
  "module": "base_engine",
  "function": "transcribe",
  "line": 123,
  "extra": {
    "request_id": "req-123",
    "processing_time": 1.5,
    "event_type": "response"
  }
}
```

## 测试

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/unit/test_base_engine.py -v

# 生成覆盖率报告
python -m pytest --cov=common tests/
```

### 测试覆盖率

目标测试覆盖率：≥80%

当前覆盖率状态：
- `base_engine.py`: 95%
- `communication.py`: 92%
- `config.py`: 88%
- `logger.py`: 85%
- `lifecycle.py`: 90%

## 最佳实践

### 1. 引擎开发

- 继承 `BaseSidecarEngine` 而不是重新实现
- 在 `_initialize_engine` 中设置引擎特定配置
- 使用 `async/await` 进行所有 I/O 操作
- 在长时间运行的操作中定期检查 `stop_event`

### 2. 错误处理

- 使用结构化异常处理
- 记录详细的错误上下文
- 区分可恢复和不可恢复的错误
- 实现适当的重试机制

### 3. 性能优化

- 使用异步 I/O 避免阻塞
- 实现批量处理减少开销
- 监控内存使用避免泄漏
- 优化模型加载和推理

### 4. 配置管理

- 使用环境变量管理敏感信息
- 实现配置验证确保正确性
- 支持热重载无需重启
- 文档化所有配置选项

## 故障排除

### 常见问题

**Q: 引擎启动失败**
A: 检查模型文件路径、设备可用性和依赖安装

**Q: 通信超时**
A: 调整 `timeout` 配置，检查网络连接

**Q: 内存泄漏**
A: 监控 `memory_usage` 指标，检查资源清理

**Q: 性能下降**
A: 查看 `processing_time` 趋势，检查系统资源

### 日志分析

```bash
# 查看错误日志
grep '"level":"ERROR"' logs/sidecar.log

# 分析性能
grep '"event_type":"performance"' logs/sidecar.log | jq '.extra.duration'

# 监控健康状态
grep '"event_type":"health_check"' logs/sidecar.log
```

## 开发指南

### 环境设置

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 代码规范

- 使用 `black` 进行代码格式化
- 使用 `flake8` 进行代码检查
- 使用 `mypy` 进行类型检查
- 遵循 PEP 8 命名规范

### 贡献指南

1. Fork 项目
2. 创建特性分支
3. 编写测试
4. 确保测试通过
5. 提交 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 更新日志

### v1.0.0 (2024-12-19)

- ✅ 完整的 Sidecar 基础架构
- ✅ 统一的引擎接口
- ✅ 进程间通信系统
- ✅ 生命周期管理
- ✅ 配置和日志系统
- ✅ 单元测试覆盖 