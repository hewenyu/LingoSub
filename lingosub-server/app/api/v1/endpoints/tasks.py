import uuid
import shutil
from pathlib import Path
import logging

from fastapi import (
    APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Response
)
from fastapi.responses import FileResponse
from celery.result import AsyncResult

from app.api.v1.schemas import TaskCreationResponse, TaskStatusResponse
from app.api.v1.dependencies import get_api_key
from app.worker.tasks import translate_srt_task
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tasks", response_model=TaskCreationResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_translation_task(
    file: UploadFile = File(...),
    target_language: str = Form(...),
    model: str = Form("gpt-4.1-mini"),
    api_key: str = Depends(get_api_key)
):
    """
    Uploads an SRT file and starts an asynchronous translation task.
    """
    logger.info(f"Received translation task: file={file.filename}, target_language={target_language}, model={model}")
    if not file.filename or not file.filename.endswith(".srt"):
        logger.warning("Invalid file type uploaded.")
        raise HTTPException(status_code=400, detail="Invalid file type. Only .srt files are accepted.")
    
    temp_dir = Path(settings.TEMP_FILE_DIR)
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / f"{uuid.uuid4()}_{file.filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File saved to {file_path}")
    finally:
        file.file.close()

    # Start the Celery task
    task = translate_srt_task.delay(
        source_file_path=str(file_path), 
        target_language=target_language,
        model=model
    )
    logger.info(f"Celery task started: task_id={task.id}")

    return {"task_id": task.id, "status": "PENDING"}


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: uuid.UUID, api_key: str = Depends(get_api_key)):
    """
    Retrieves the current status of a translation task.
    """
    logger.info(f"Checking status for task_id={task_id}")
    task_result = AsyncResult(str(task_id), app=translate_srt_task.app)
    
    response_data = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.status == 'PENDING':
        pass
    elif task_result.status == "PROCESSING":
        response_data["progress"] = task_result.info.get("progress", 0)
    elif task_result.status == "SUCCESS":
        response_data["progress"] = 1.0
    elif task_result.status == "FAILURE":
        response_data["error_message"] = str(task_result.info)
    
    logger.info(f"Task status for task_id={task_id}: {response_data}")
    return response_data

@router.get("/tasks/{task_id}/result", response_class=FileResponse)
async def get_task_result(task_id: uuid.UUID, api_key: str = Depends(get_api_key)):
    """
    Retrieves the result of a completed translation task.
    """
    logger.info(f"Retrieving result for task_id={task_id}")
    task_result = AsyncResult(str(task_id), app=translate_srt_task.app)

    if not task_result.ready():
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result not available. Task status is: {task_result.status}"
        )
    
    if task_result.failed():
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task failed. Error: {str(task_result.info)}"
        )
    
    result = task_result.get()
    result_path = Path(result["result_path"])

    if not result_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result file not found."
        )

    logger.info(f"Result file found: {result_path}")
    return FileResponse(
        path=result_path,
        media_type="application/x-subrip",
        filename=f"translated_{task_id}.srt"
    )