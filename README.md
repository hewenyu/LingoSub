# LingoSub
AI字幕翻译工具


```bash
# worker
celery -A app.worker.celery_app worker --loglevel=info --concurrency=2


# api 
uvicorn app.main:app --reload --port 8001



# post
curl -X POST "http://127.0.0.1:8001/api/v1/tasks" ^
  -H "Authorization: Bearer test" ^
  -F "file=@Black.Angel.2002.iNT.DVDRip.xVID-xHONG.chs.srt" ^
  -F "target_language=en"

# windows
curl.exe -X POST "http://127.0.0.1:8001/api/v1/tasks" -H "Authorization: Bearer test" -F "file=@Black.Angel.2002.iNT.DVDRip.xVID-xHONG.chs.srt" -F "target_language=en"

```