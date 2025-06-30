import logging
from typing import Optional, List
from openai import OpenAI, APIError, RateLimitError
import time
import random

from app.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Define a threshold for switching to single-line translation
MIN_BATCH_SIZE_FOR_RECURSION = 10

class TranslationService:
    """
    A service to handle interactions with the OpenAI API for translation.
    """
    def __init__(self, api_key: str, model: str, rate_limiter: RateLimiter, base_url: Optional[str] = None):
        if not api_key:
            raise ValueError("API key is required.")
        self.client = OpenAI(api_key=api_key, base_url=base_url, max_retries=0) # Disable internal retries
        self.model = model
        self.rate_limiter = rate_limiter

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
        self.rate_limiter.acquire()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate the following text to {target_language}."},
                {"role": "user", "content": text},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def translate_batch(self, text_batch: str, target_language: str, max_retries: int = 2) -> str:
        """
        Translates a batch of text using a recursive, hierarchical fallback strategy.
        """
        original_texts = text_batch.split('|||')
        expected_count = len(original_texts)

        # If the batch is too small, just translate line-by-line directly.
        if expected_count < MIN_BATCH_SIZE_FOR_RECURSION:
            return self._fallback_to_single_lines(original_texts, target_language)

        system_prompt, user_prompt = self._create_prompt(text_batch, target_language)
        attempt = 0
        while attempt < max_retries:
            try:
                self.rate_limiter.acquire()
                logger.info(f"Attempting to translate a batch of {expected_count} subtitles. Attempt {attempt + 1}/{max_retries}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                )
                
                if not response.choices or not response.choices[0].message.content:
                    raise ValueError("Received empty or invalid content from API.")
                
                translated_text = response.choices[0].message.content.strip()
                translated_parts = translated_text.split('|||')
                
                if len(translated_parts) == expected_count:
                    logger.info(f"Successfully translated batch of {expected_count} with correct format.")
                    return translated_text
                else:
                    logger.warning(
                        f"Format mismatch in batch of {expected_count}. "
                        f"Expected {expected_count}, got {len(translated_parts)}. Retrying..."
                    )
                    attempt += 1
                    continue

            except (APIError, RateLimitError) as e:
                logger.error(f"API error on batch of {expected_count}: {e}", exc_info=True)
                attempt += 1
            except Exception as e:
                logger.error(f"Unexpected error on batch of {expected_count}: {e}", exc_info=True)
                attempt += 1
        
        # --- Hierarchical Fallback ---
        logger.warning(f"Batch of {expected_count} failed after {max_retries} attempts. Splitting and retrying.")
        mid_point = expected_count // 2
        
        first_half_batch = "|||".join(original_texts[:mid_point])
        second_half_batch = "|||".join(original_texts[mid_point:])

        first_half_translated = self.translate_batch(first_half_batch, target_language)
        second_half_translated = self.translate_batch(second_half_batch, target_language)
        
        return f"{first_half_translated}|||{second_half_translated}"

    def _fallback_to_single_lines(self, original_texts: List[str], target_language: str) -> str:
        """
        The final fallback mechanism: translates text line by line.
        """
        logger.warning(f"Falling back to single-line translation for a batch of {len(original_texts)} subtitles.")
        translated_parts = []
        for text in original_texts:
            try:
                translated_parts.append(self._translate_single_text(text, target_language))
            except Exception as e:
                logger.error(f"Failed to translate single line '{text[:30]}...' during fallback: {e}", exc_info=True)
                translated_parts.append(f"[Translation Error: {text}]")
        
        return "|||".join(translated_parts) 