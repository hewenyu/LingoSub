import logging
from pathlib import Path
import uuid
from celery import Task
import redis

from app.worker.celery_app import celery_app
from app.core.config import settings
from app.services.srt_processor import SRTProcessor
from app.services.translation_service import TranslationService
from app.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Initialize a global Redis client for the worker
# This helps in reusing the connection across tasks if the worker process is the same.
try:
    redis_client = redis.from_url(settings.CELERY_BROKER_URL)
    logger.info("Successfully connected to Redis for Rate Limiter.")
except Exception as e:
    logger.error(f"Failed to connect to Redis for Rate Limiter: {e}", exc_info=True)
    redis_client = None

@celery_app.task(bind=True)
def translate_srt_task(self: Task, source_file_path: str, target_language: str, model: str):
    """
    A Celery task to translate an SRT file.
    Orchestrates SRT processing and translation services.
    """
    logger.info(f"Task {self.request.id} started: file={source_file_path}, lang={target_language}, model={model}")
    
    if not redis_client:
        raise ConnectionError("Redis client is not available. Cannot proceed with rate limiting.")

    try:
        self.update_state(state='PROCESSING', meta={'progress': 0.05, 'message': 'Initializing...'})
        
        # 1. Initialize Services with Rate Limiter
        rate_limiter = RateLimiter(
            redis_client=redis_client,
            key="openai_api_limit",
            limit=1,  # 1 request
            period=2  # per 2 seconds
        )
        processor = SRTProcessor(file_path=source_file_path)
        translator = TranslationService(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model=model,
            rate_limiter=rate_limiter
        )

        # 2. Parse and Batch
        self.update_state(state='PROCESSING', meta={'progress': 0.1, 'message': 'Parsing SRT file...'})
        processor.parse()
        batches = processor.batch_for_translation()
        
        if not batches:
            logger.warning("No text found in SRT file for translation.")
            # If the file is empty, we can consider it a success with an empty result.
            result_path = _get_result_path(source_file_path)
            processor.write(str(result_path))
            return {"result_path": str(result_path)}

        # 3. Translate
        self.update_state(state='PROCESSING', meta={'progress': 0.3, 'message': 'Translating...'})
        translated_batches = []
        num_batches = len(batches)
        start_progress = 0.3
        end_progress = 0.8
        
        for i, batch in enumerate(batches):
            progress = start_progress + (i / num_batches) * (end_progress - start_progress)
            self.update_state(
                state='PROCESSING', 
                meta={'progress': round(progress, 2), 'message': f'Translating batch {i+1}/{num_batches}...'}
            )
            logger.debug(f"Task {self.request.id}: Translating batch {i+1}/{num_batches}")
            translated_batch = translator.translate_batch(batch, target_language)
            translated_batches.append(translated_batch)

        # 4. Reconstruct
        self.update_state(state='PROCESSING', meta={'progress': 0.8, 'message': 'Reconstructing file...'})
        processor.reconstruct(translated_batches)

        # 5. Save Result
        self.update_state(state='PROCESSING', meta={'progress': 0.9, 'message': 'Saving result...'})
        result_path = _get_result_path(source_file_path)
        processor.write(str(result_path))

        logger.info(f"Task {self.request.id} completed. Result saved to {result_path}")
        # The final state is automatically set to SUCCESS upon return
        return {"result_path": str(result_path), "progress": 1.0}

    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e

def _get_result_path(source_file_path: str) -> Path:
    """Generates a unique path for the translated file."""
    source_p = Path(source_file_path)
    result_dir = Path(settings.RESULT_FILE_DIR)
    result_dir.mkdir(exist_ok=True)
    return result_dir / f"translated_{uuid.uuid4().hex[:8]}_{source_p.name}"