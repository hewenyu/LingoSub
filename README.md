# LingoSub
AI字幕翻译工具


```bash
# worker
celery -A app.worker.celery_app worker --loglevel=info --concurrency=2

# windows woker 
celery -A app.worker.celery_app worker --loglevel=info --concurrency=1


# api 
uvicorn app.main:app --reload --port 8001



# linux
curl -X POST "http://127.0.0.1:8001/api/v1/tasks" -H "Authorization: Bearer test" -F "file=@kung.fu.dunk.2008.dvdrip.xvid-bien.srt" -F "target_language=zh"

# windows
curl.exe -X POST "http://127.0.0.1:8001/api/v1/tasks" -H "Authorization: Bearer test" -F "file=@kung.fu.dunk.2008.dvdrip.xvid-bien.srt" -F "target_language=zh"
```


```bash
# status /tasks/{task_id}/status
curl -X GET "http://127.0.0.1:8001/api/v1/tasks/da69f276-5579-47da-8cf4-c7683999cb31/status" -H "Authorization: Bearer test"
```