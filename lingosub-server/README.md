# LingoSub Server

本仓库为 LingoSub 项目的服务端部分，基于 FastAPI 和 Celery 构建。

## 功能

- 接收 SRT 字幕文件上传
- 使用大语言模型进行异步翻译
- 提供任务状态查询和结果下载接口

## 安装与启动

1.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

2.  **配置环境变量**
    创建一个 `.env` 文件并设置所需的环境变量：
    ```
    API_KEY="your_secret_key"
    CELERY_BROKER_URL="redis://localhost:6379/0"
    CELERY_RESULT_BACKEND="redis://localhost:6379/0"
    ```

3.  **启动 Celery Worker**
    ```bash
    celery -A app.worker.celery_app worker --loglevel=info
    ```

4.  **启动 FastAPI 服务**
    ```bash
    uvicorn app.main:app --reload
    ``` 