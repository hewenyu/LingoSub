import logging
from typing import Optional, List, Dict, Any
import json
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

    def _create_prompt(self, json_batch_str: str, target_language: str) -> str:
        """
        Creates a specialized prompt for batch translation using JSON format.
        """
        system_prompt = f"""You are a professional subtitle translator. Your task is to translate the `text` field of each JSON object in the following array into {target_language}.
You MUST respond with a valid JSON array with the exact same structure and number of objects as the input.
Do NOT alter the `index`, `start`, or `end` fields. Only modify the `text` field with its translation.

Example Input:
[
  {{
    "index": 1,
    "start": "00:00:01,000",
    "end": "00:00:03,000",
    "text": "Hello, everyone!"
  }}
]

Example Output for 'Spanish':
[
  {{
    "index": 1,
    "start": "00:00:01,000",
    "end": "00:00:03,000",
    "text": "¡Hola a todos!"
  }}
]
"""
        user_prompt = f"Translate the `text` in the following JSON array to {target_language}:\n\n{json_batch_str}"
        return system_prompt, user_prompt

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

    def translate_batch(self, batch: List[Dict[str, Any]], target_language: str, max_retries: int = 2) -> List[Dict[str, Any]]:
        """
        Translates a batch of subtitle dicts using a recursive, hierarchical fallback strategy.
        """
        expected_count = len(batch)
        if expected_count == 0:
            return []

        if expected_count < MIN_BATCH_SIZE_FOR_RECURSION:
            return self._fallback_to_single_items(batch, target_language)

        json_batch_str = json.dumps(batch, indent=2)
        system_prompt, user_prompt = self._create_prompt(json_batch_str, target_language)
        
        attempt = 0
        while attempt < max_retries:
            try:
                self.rate_limiter.acquire()
                logger.info(f"Attempting to translate a batch of {expected_count} subtitles. Attempt {attempt + 1}/{max_retries}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                )
                
                translated_text = response.choices[0].message.content
                translated_data = json.loads(translated_text)
                
                # The response might be a dict with a key containing the list
                if isinstance(translated_data, dict):
                     # A common pattern is for the model to wrap the list in a key
                     if len(translated_data.keys()) == 1:
                         key = list(translated_data.keys())[0]
                         if isinstance(translated_data[key], list):
                             translated_data = translated_data[key]

                if isinstance(translated_data, list) and len(translated_data) == expected_count:
                    logger.info(f"Successfully translated batch of {expected_count} with correct format.")
                    return translated_data
                else:
                    logger.warning(f"Format/count mismatch in batch of {expected_count}. Retrying...")
                    attempt += 1

            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from API response on attempt {attempt + 1}", exc_info=True)
                attempt += 1
            except Exception as e:
                logger.error(f"Unexpected error on batch of {expected_count}: {e}", exc_info=True)
                attempt += 1
        
        logger.warning(f"Batch of {expected_count} failed after {max_retries} attempts. Splitting and retrying.")
        mid_point = expected_count // 2
        
        first_half_translated = self.translate_batch(batch[:mid_point], target_language)
        second_half_translated = self.translate_batch(batch[mid_point:], target_language)
        
        return first_half_translated + second_half_translated

    def _fallback_to_single_items(self, batch: List[Dict[str, Any]], target_language: str) -> List[Dict[str, Any]]:
        logger.warning(f"Falling back to single-item translation for a batch of {len(batch)} subtitles.")
        translated_items = []
        for item in batch:
            try:
                translated_text = self._translate_single_text(item['text'], target_language)
                new_item = item.copy()
                new_item['text'] = translated_text
                translated_items.append(new_item)
            except Exception as e:
                logger.error(f"Failed to translate single item '{item.get('text', '')[:30]}...' during fallback: {e}", exc_info=True)
                error_item = item.copy()
                error_item['text'] = f"[Translation Error: {item.get('text', '')}]"
                translated_items.append(error_item)
        return translated_items 