import logging
from typing import Optional, List, Dict, Any
import json
import re
from openai import OpenAI, APIError, RateLimitError
import time
import random

from app.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Define a threshold for switching to single-line translation
MIN_BATCH_SIZE_FOR_RECURSION = 5

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

    def _create_numbered_list_prompt(self, numbered_list: str, target_language: str) -> tuple[str, str]:
        system_prompt = f"""You are a professional translator. Your task is to translate the text for each numbered line into {target_language}.
You MUST respond with a numbered list that has the exact same number of lines as the input.
Do NOT add any extra text, explanations, or introductory phrases. Only provide the translated numbered list.

Example Input:
1. Hello, everyone!
2. Welcome to our channel.

Example Output for 'Spanish':
1. ¡Hola a todos!
2. Bienvenidos a nuestro canal.
"""
        user_prompt = f"Translate the text for each line in the following numbered list to {target_language}:\n\n{numbered_list}"
        return system_prompt, user_prompt

    def _parse_numbered_list(self, text: str) -> List[str]:
        # Split by lines, then strip numbering like "1. ", "12. ", etc.
        lines = text.strip().split('\n')
        # This regex handles numbers, dots, and optional spaces.
        return [re.sub(r'^\d+\.\s*', '', line).strip() for line in lines]

    def _get_numbered_text_map(self, text: str) -> Dict[int, str]:
        """Parses a numbered list string into a dictionary."""
        result_map = {}
        lines = text.strip().split('\n')
        for line in lines:
            match = re.match(r'^(\d+)\.\s*(.*)', line.strip())
            if match:
                index = int(match.group(1))
                content = match.group(2).strip()
                result_map[index] = content
        return result_map

    def _translate_single_text(self, text: str, target_language: str) -> str:
        """
        Translates a single line of text. Used as a fallback.
        """
        self.rate_limiter.acquire()
        logger.info(f"Translating single line to {target_language}: '{text[:30]}...'")
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

        # Format the batch into a numbered list string
        numbered_list = "\n".join([f"{i+1}. {item['text']}" for i, item in enumerate(batch)])
        system_prompt, user_prompt = self._create_numbered_list_prompt(numbered_list, target_language)
        
        attempt = 0
        while attempt < max_retries:
            try:
                self.rate_limiter.acquire()
                logger.info(f"Attempting to translate a batch of {expected_count} translation units. Attempt {attempt + 1}/{max_retries}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                )
                
                translated_text = response.choices[0].message.content.strip()
                
                # --- Surgical Retry Logic ---
                # This logic is more robust than just comparing counts.
                translated_map = self._get_numbered_text_map(translated_text)
                
                if len(translated_map) == expected_count:
                    logger.info(f"Successfully translated batch of {expected_count} with correct format.")
                    reconstructed_batch = []
                    for i, item in enumerate(batch):
                        new_item = item.copy()
                        # Use the map to ensure we get the right text even if order is scrambled
                        new_item['text'] = translated_map.get(i + 1, "[Translation Missing]")
                        reconstructed_batch.append(new_item)
                    return reconstructed_batch
                
                # If count mismatches, try to repair it.
                logger.warning(
                    f"Count mismatch in batch of {expected_count}. "
                    f"Expected {expected_count}, got {len(translated_map)}. Attempting surgical retry."
                )
                
                repaired_batch = []
                for i, item in enumerate(batch):
                    new_item = item.copy()
                    original_text_number = i + 1

                    if original_text_number in translated_map:
                        new_item['text'] = translated_map[original_text_number]
                    else:
                        logger.warning(f"Item {original_text_number} was missing from LLM response. Translating it individually.")
                        try:
                            new_item['text'] = self._translate_single_text(item['text'], target_language)
                        except Exception as e:
                            logger.error(f"Surgical retry for item {original_text_number} failed: {e}")
                            new_item['text'] = f"[Translation Error: {item['text']}]"
                    
                    repaired_batch.append(new_item)
                
                logger.info(f"Successfully repaired batch of {expected_count} via surgical retry.")
                return repaired_batch
                # --- End Surgical Retry ---

            except Exception as e:
                logger.error(f"Unexpected error on batch of {expected_count}, will trigger fallback: {e}", exc_info=True)
                attempt += 1 # Incrementing here means we won't retry on parsing/validation errors, but go to fallback.
        
        # This fallback is now a secondary safety net.
        logger.warning(f"Batch of {expected_count} failed even surgical retry. Falling back to splitting.")
        mid_point = expected_count // 2
        
        first_half_translated = self.translate_batch(batch[:mid_point], target_language)
        second_half_translated = self.translate_batch(batch[mid_point:], target_language)
        
        return first_half_translated + second_half_translated

    def _fallback_to_single_items(self, batch: List[Dict[str, Any]], target_language: str) -> List[Dict[str, Any]]:
        logger.warning(f"Falling back to single-item translation for a batch of {len(batch)} translation units.")
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