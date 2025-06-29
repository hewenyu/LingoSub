# 核心处理流程时序图

本文档使用 Mermaid 语法绘制时序图，以描述从客户端发起翻译请求到最终获取结果的完整端到端流程。

## 成功流程

此图展示了一个翻译任务成功完成的典型交互过程。

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant FastAPI as FastAPI 服务
    participant Celery as Celery 任务队列
    participant Worker as Celery Worker
    participant Translator as 翻译服务
    participant LLM_API as 外部 LLM API
    participant Storage as 文件存储

    Client->>+FastAPI: POST /api/v1/tasks (上传 SRT 文件)
    FastAPI->>+Celery: T1: 调用 start_translation.delay() 创建任务
    FastAPI-->>-Client: 202 Accepted (返回 task_id)
    Celery-->>-Worker: T2: 分发任务给空闲 Worker
    
    Worker->>+Translator: T3: 执行翻译任务
    Translator->>+LLM_API: T4: 调用大语言模型进行翻译
    LLM_API-->>-Translator: 返回翻译结果
    Translator->>+Storage: T5: 保存翻译后的 SRT 文件
    Storage-->>-Translator: 确认保存成功
    Translator-->>-Worker: 任务完成
    Worker->>Celery: T6: 更新任务状态为 SUCCESS
    
    loop 轮询任务状态
        Client->>+FastAPI: GET /api/v1/tasks/{task_id}/status
        FastAPI->>Celery: 获取任务状态
        alt 任务处理中
            Celery-->>FastAPI: 返回 "PROCESSING"
            FastAPI-->>-Client: 200 OK (返回 "PROCESSING")
        else 任务已完成
            Celery-->>FastAPI: 返回 "SUCCESS"
            FastAPI-->>-Client: 200 OK (返回 "SUCCESS")
        end
    end

    Client->>+FastAPI: GET /api/v1/tasks/{task_id}/result
    FastAPI->>+Storage: 读取已翻译的 SRT 文件
    Storage-->>FastAPI: 返回文件内容
    FastAPI-->>-Client: 200 OK (返回 SRT 文件)
```

## 流程说明

1.  **T1: 创建任务**
    - 客户端上传文件，FastAPI 接收到请求后，立即将翻译作业（包含文件引用和目标语言）推送到 Celery 消息队列中，并马上向客户端返回一个唯一的 `task_id`。这使得 API 不会被长时间运行的翻译过程所阻塞。

2.  **T2: 任务分发**
    - Celery Broker（如 Redis）将任务分发给一个已订阅的、空闲的 Celery Worker 进程。

3.  **T3: 执行任务**
    - Worker 开始执行任务，调用核心的 `翻译服务` 模块。

4.  **T4: 调用 AI 模型**
    - `翻译服务` 负责与外部的大语言模型 API 进行交互，发送待翻译的文本并获取结果。

5.  **T5: 存储结果**
    - 翻译完成后，结果将被保存到持久化存储中（例如本地文件系统或云存储）。

6.  **T6: 更新状态**
    - Worker 在任务成功后，通过 Celery Backend（如 Redis）更新任务的最终状态为 `SUCCESS`。如果中途发生任何错误，状态将被更新为 `FAILURE`。 