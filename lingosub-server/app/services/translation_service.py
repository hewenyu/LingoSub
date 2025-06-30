import logging
from typing import Optional
from openai import OpenAI, APIError, RateLimitError
import time
import random

logger = logging.getLogger(__name__)

class TranslationService:
    """
    A service to handle interactions with the OpenAI API for translation.
    """
    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        if not api_key:
            raise ValueError("API key is required.")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def _create_prompt(self, text_batch: str, target_language: str) -> str:
        """
        Creates a specialized prompt for batch translation.
        """
        system_prompt = (
            "You are a professional subtitle translator. "
            "Translate the following text into a natural-sounding {target_language}. "
            "The input consists of multiple subtitle entries separated by '|||'. "
            "CRITICALLY, you must maintain this '|||' separator for each entry in your translation output. "
            "The number of '|||' separators in your output MUST be exactly the same as in the input. "
            "For example, if the input is 'Hello|||How are you?', your output in Spanish must be 'Hola|||¿Cómo estás?'."
        )
        
        user_prompt = f"Translate the following subtitle content into {target_language}:\n\n---\n{text_batch}\n---"

        return system_prompt.format(target_language=target_language), user_prompt

    def _translate_single_text(self, text: str, target_language: str) -> str:
        """
        Translates a single line of text. Used as a fallback.
        """
        logger.debug(f"Translating single line to {target_language}: '{text[:30]}...'")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate the following text to {target_language}."},
                {"role": "user", "content": text},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def translate_batch(self, text_batch: str, target_language: str, max_retries: int = 3) -> str:
        """
        Translates a batch of text using the OpenAI API with retry logic.
        If batch translation fails format validation, it falls back to single-line translation.
        """
        original_texts = text_batch.split('|||')
        expected_count = len(original_texts)

        system_prompt, user_prompt = self._create_prompt(text_batch, target_language)
        attempt = 0
        while attempt < max_retries:
            try:
                logger.info(f"Translating batch for {target_language}. Attempt {attempt + 1}/{max_retries}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                )
                
                if not response.choices or not response.choices[0].message.content:
                    logger.warning(f"API returned an empty response for batch. Attempt {attempt + 1}/{max_retries}")
                    raise ValueError("Received empty or invalid content from API.")
                
                translated_text = response.choices[0].message.content.strip()
                
                # --- Validation Step ---
                translated_parts = translated_text.split('|||')
                if len(translated_parts) == expected_count:
                    logger.info(f"Successfully translated batch for {target_language} with correct format.")
                    return translated_text
                else:
                    logger.warning(
                        f"Format mismatch in batch translation. "
                        f"Expected {expected_count} parts, got {len(translated_parts)}. "
                        f"Attempt {attempt + 1}/{max_retries}. Retrying..."
                    )
                    # This will be retried by the loop
                    if attempt + 1 >= max_retries:
                        break # Break to fall back to single-line translation
                    attempt += 1
                    time.sleep(2) # Wait before retrying on format mismatch
                    continue
                # --- End Validation ---

            except RateLimitError as e:
                wait_time = (2 ** attempt) + (2 * random.random()) # Exponential backoff with jitter
                logger.warning(f"Rate limit hit on attempt {attempt+1}. Retrying in {wait_time:.2f}s... Error: {e}")
                time.sleep(wait_time)
                attempt += 1
            except APIError as e:
                logger.error(f"API error on attempt {attempt+1} during translation: {e}", exc_info=True)
                # For specific status codes, we might not want to retry
                if e.status_code in [400, 404, 401]:
                     raise e
                attempt +=1
                time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"An unexpected error occurred on attempt {attempt+1} during translation: {e}", exc_info=True)
                attempt += 1
                if attempt >= max_retries:
                    raise
                time.sleep(2) # Brief wait before retrying on general errors

        # --- Fallback Mechanism ---
        logger.warning(f"Batch translation failed format validation after {max_retries} attempts. "
                       f"Falling back to single-line translation for a batch of {expected_count} subtitles.")
        
        translated_parts = []
        for i, text in enumerate(original_texts):
            try:
                # Adding a small delay to avoid hitting rate limits in the fallback
                if i > 0:
                    time.sleep(0.1)
                translated_parts.append(self._translate_single_text(text, target_language))
            except Exception as e:
                logger.error(f"Failed to translate single line '{text[:30]}...' during fallback: {e}", exc_info=True)
                # If a single line fails, we add a placeholder to maintain structure.
                translated_parts.append(f"[Translation Error: {text}]")
        
        logger.info("Successfully completed fallback translation.")
        return "|||".join(translated_parts) 