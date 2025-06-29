import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from celery.result import AsyncResult

from app.api.v1.schemas import TaskCreationResponse, TaskStatusResponse
from app.api.v1.dependencies import get_api_key
from app.worker.tasks import translate_srt_task

router = APIRouter()


@router.post("/tasks", response_model=TaskCreationResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_translation_task(
    target_language: str = Form(...),
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
):
    """
    Uploads an SRT file and starts an asynchronous translation task.
    """
    if not file.filename.endswith(".srt"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .srt files are accepted.")
    
    # Save the uploaded file temporarily
    # NOTE: In a production environment, this should be a more robust solution,
    # like uploading to a cloud storage (e.g., S3/R2).
    temp_dir = Path("temp_files")
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / f"{uuid.uuid4()}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Start the Celery task
    task = translate_srt_task.delay(source_file_path=str(file_path), target_language=target_language)

    return {"task_id": task.id, "status": "PENDING"}


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: uuid.UUID, api_key: str = Depends(get_api_key)):
    """
    Retrieves the current status of a translation task.
    """
    task_result = AsyncResult(str(task_id), app=translate_srt_task.app)
    
    response_data = {
        "task_id": task_id,
        "status": task_result.status,
    }

    if task_result.status == "PROCESSING":
        response_data["progress"] = task_result.info.get("progress", 0)
    elif task_result.status == "FAILURE":
        response_data["error_message"] = str(task_result.info)

    return response_data

@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: uuid.UUID, api_key: str = Depends(get_api_key)):
    """
    Retrieves the result of a completed translation task.
    NOTE: This is a placeholder. The actual implementation will return a file response.
    """
    task_result = AsyncResult(str(task_id), app=translate_srt_task.app)

    if not task_result.ready():
        raise HTTPException(status_code=404, detail=f"Result not available. Task status is: {task_result.status}")
    
    if task_result.failed():
         raise HTTPException(status_code=404, detail=f"Task failed. Error: {str(task_result.info)}")

    # In a real implementation, you would fetch the file from storage
    # using the path returned by the task.
    # from fastapi.responses import FileResponse
    # result_path = task_result.result.get("result_path")
    # return FileResponse(result_path, media_type="application/x-subrip", filename="translated.srt")

    return {"message": "Task completed successfully. This is a placeholder for the result file.", "result": task_result.result} 