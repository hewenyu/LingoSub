import logging
import pysrt
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class SRTProcessor:
    """
    Handles reading, parsing, processing, and writing SRT files.
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
            self.original_texts = [sub.text for sub in self.subs]
            logger.info(f"Successfully parsed {len(self.subs)} subtitle entries.")
        except Exception as e:
            logger.error(f"Failed to parse SRT file {self.file_path}: {e}", exc_info=True)
            raise

    def batch_for_translation(self, batch_size: int = 100) -> List[str]:
        """
        Creates batches of text for translation based on a specified batch size.
        
        :param batch_size: The number of subtitle entries per batch.
        :return: A list of string batches.
        """
        if not self.subs:
            self.parse()
        
        if not self.original_texts:
            logger.warning("No original texts found to batch.")
            return []
            
        logger.info(f"Batching {len(self.original_texts)} texts into chunks of {batch_size}.")
        
        batches = []
        for i in range(0, len(self.original_texts), batch_size):
            batch_texts = self.original_texts[i:i + batch_size]
            batches.append(self.SUBTITLE_SEPARATOR.join(batch_texts))
            logger.debug(f"Created batch {len(batches)} with {len(batch_texts)} entries.")
            
        logger.info(f"Successfully created {len(batches)} batches.")
        return batches

    def reconstruct(self, translated_batches: List[str]):
        """
        Reconstructs the subtitles with the translated text.
        """
        if not self.subs:
            raise ValueError("Subtitles have not been parsed yet. Call parse() first.")
        
        logger.info("Reconstructing subtitles from translated batches.")
        
        all_translated_texts = []
        for i, batch in enumerate(translated_batches):
            texts = batch.split(self.SUBTITLE_SEPARATOR)
            logger.debug(f"Processing translated batch {i+1} with {len(texts)} entries.")
            all_translated_texts.extend(texts)

        if len(all_translated_texts) != len(self.subs):
            error_msg = f"Mismatch between original ({len(self.subs)}) and translated ({len(all_translated_texts)}) subtitle counts."
            logger.error(error_msg)
            raise ValueError(error_msg)

        for i, sub in enumerate(self.subs):
            sub.text = all_translated_texts[i].strip()
        
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