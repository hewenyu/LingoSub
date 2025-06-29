import uuid
from pathlib import Path
import logging
from app.worker.celery_app import celery_app
from app.services.translator import translate_file

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def translate_srt_task(self, source_file_path: str, target_language: str, model: str):
    """
    A Celery task to translate an SRT file by calling the translation service.
    """
    logger.info(f"Celery task started: source_file_path={source_file_path}, target_language={target_language}, model={model}")
    try:
        source_path = Path(source_file_path)

        # Define a callback function that updates the Celery task's state
        def update_progress(progress: float):
            self.update_state(state='PROCESSING', meta={'progress': progress})
            logger.info(f"Task progress: {progress*100:.2f}%")

        result_path = translate_file(
            source_path=source_path, 
            target_language=target_language, 
            model=model,
            update_callback=update_progress
        )
        logger.info(f"Translation completed. Result saved to {result_path}")
        return {"result_path": str(result_path)}
    except Exception as e:
        logger.error(f"Task failed: {e}")
        self.update_state(state='FAILURE', meta={'error_message': str(e)})
        # Re-raise the exception to let Celery know the task failed
        raise e