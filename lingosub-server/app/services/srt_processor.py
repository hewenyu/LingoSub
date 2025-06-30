import logging
import pysrt
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SRTProcessor:
    """
    Handles reading, parsing, processing, and writing SRT files.
    Uses a list of dictionaries as the intermediate format.
    """
    SUBTITLE_SEPARATOR = "|||"

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.is_file():
            raise FileNotFoundError(f"SRT file not found at {file_path}")
        self.subs = None
        self.original_texts = []

    def parse(self):
        """
        Parses the SRT file into a list of subtitle objects.
        """
        logger.info(f"Parsing SRT file: {self.file_path}")
        try:
            self.subs = pysrt.open(str(self.file_path), encoding='utf-8')
            # self.original_texts = [sub.text for sub in self.subs]
            logger.info(f"Successfully parsed {len(self.subs)} subtitle entries.")
        except Exception as e:
            logger.error(f"Failed to parse SRT file {self.file_path}: {e}", exc_info=True)
            raise

    def batch_for_translation(self, batch_size: int = 100) -> List[List[Dict[str, Any]]]:
        """
        Creates batches of subtitle objects for translation.
        
        :param batch_size: The number of subtitle entries per batch.
        :return: A list of batches, where each batch is a list of subtitle dicts.
        """
        if not self.subs:
            self.parse()
        
        if not self.subs:
            logger.warning("No subtitles found to batch.")
            return []
            
        logger.info(f"Batching {len(self.subs)} subtitles into chunks of {batch_size}.")
        
        subtitle_dicts = [
            {
                "index": sub.index,
                "start": str(sub.start),
                "end": str(sub.end),
                "text": sub.text
            } for sub in self.subs
        ]
        
        batches = [subtitle_dicts[i:i + batch_size] for i in range(0, len(subtitle_dicts), batch_size)]
        logger.info(f"Successfully created {len(batches)} batches.")
        return batches

    def reconstruct(self, translated_dicts: List[Dict[str, Any]]):
        """
        Reconstructs the subtitles with the translated text from a list of dicts.
        """
        if not self.subs:
            raise ValueError("Subtitles have not been parsed yet. Call parse() first.")
        
        logger.info(f"Reconstructing subtitles from {len(translated_dicts)} translated dicts.")

        if len(translated_dicts) != len(self.subs):
            error_msg = f"Mismatch between original ({len(self.subs)}) and translated ({len(translated_dicts)}) subtitle counts."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Assuming the translated_dicts are in the correct order.
        # A more robust implementation could use the index for matching.
        for i, sub in enumerate(self.subs):
            translated_data = translated_dicts[i]
            # Safety check for index if needed
            if translated_data.get('index') != sub.index:
                 logger.warning(f"Index mismatch during reconstruction. Expected {sub.index}, got {translated_data.get('index')}. Relying on list order.")
            sub.text = translated_data['text'].strip()
        
        logger.info("Successfully reconstructed subtitles.")

    def write(self, output_path: str):
        """
        Saves the processed subtitles to a new SRT file.
        """
        if not self.subs:
            raise ValueError("No subtitles to write. Process a file first.")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving processed subtitles to {output_path}")
        try:
            self.subs.save(str(output_path), encoding='utf-8')
            logger.info("File saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save SRT file to {output_path}: {e}", exc_info=True)
            raise 