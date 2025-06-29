import uuid
from pathlib import Path
from app.worker.celery_app import celery_app
from app.services.translator import translate_file


@celery_app.task(bind=True)
def translate_srt_task(self, source_file_path: str, target_language: str, model: str):
    """
    A Celery task to translate an SRT file by calling the translation service.
    """
    try:
        source_path = Path(source_file_path)
        
        result_path = translate_file(
            source_path=source_path, 
            target_language=target_language, 
            model=model
        )
        
        return {"result_path": str(result_path)}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error_message': str(e)})
        # Re-raise the exception to let Celery know the task failed
        raise e