# LingoSub
AI字幕翻译工具


```bash
# worker
celery -A app.worker.celery_app worker --loglevel=info --concurrency=2


# api 
uvicorn app.main:app --reload --port 8001
```