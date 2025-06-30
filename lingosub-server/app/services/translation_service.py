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
            "Please maintain this '|||' separator in your translation output. "
            "Ensure the translation is accurate and preserves the original tone."
        )
        
        user_prompt = f"Translate the following subtitle content into {target_language}:\n\n---\n{text_batch}\n---"

        return system_prompt.format(target_language=target_language), user_prompt

    def translate_batch(self, text_batch: str, target_language: str, max_retries: int = 3) -> str:
        """
        Translates a batch of text using the OpenAI API with retry logic.
        """
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
                translated_text = response.choices[0].message.content
                logger.info("Successfully translated batch.")
                return translated_text.strip()
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

        raise Exception(f"Failed to translate batch for {target_language} after {max_retries} retries.") 