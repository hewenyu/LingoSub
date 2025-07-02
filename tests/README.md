# 测试模块

LingoSub 项目的完整测试体系，确保代码质量和功能稳定性。

## 测试结构

### 单元测试 (`unit/`)
- **Python 引擎测试**：FunASR、Whisper 引擎单元测试
- **Rust 后端测试**：Tauri 命令、服务逻辑测试
- **前端组件测试**：React 组件、Hooks 测试
- **工具函数测试**：公共工具库测试

### 集成测试 (`integration/`)
- **端到端流程**：完整的字幕生成工作流测试
- **Sidecar 通信**：进程间通信协议测试
- **API 接口测试**：前后端接口集成测试
- **性能基准测试**：处理速度和资源使用测试

### 测试数据 (`fixtures/`)
- **音频样本**：各种格式和语言的测试音频
- **字幕文件**：标准格式的参考字幕
- **配置样例**：测试用的配置文件
- **Mock 数据**：模拟数据和响应

## 测试规范

### 覆盖率要求
- 单元测试覆盖率 ≥ 80%
- 关键业务逻辑覆盖率 ≥ 95%
- 边界条件和异常处理完整覆盖

### 性能基准
- FunASR 引擎：RTF < 0.5
- Whisper 引擎：RTF < 0.3
- Netflix 处理器：处理速度 > 100 字幕/秒
- 内存使用：峰值 < 4GB

### 测试环境
- **本地开发**：pytest + Jest 快速测试
- **CI/CD**：GitHub Actions 自动化测试
- **性能测试**：定期性能回归测试
- **兼容性测试**：多平台、多版本测试

## 运行测试

```bash
# Python 单元测试
pytest tests/unit/python/

# Rust 单元测试  
cd LingoSub-cli && cargo test

# 前端测试
cd LingoSub-cli && npm test

# 集成测试
pytest tests/integration/

# 性能基准测试
pytest tests/integration/benchmarks/
``` 