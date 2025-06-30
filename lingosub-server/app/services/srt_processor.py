import logging
import pysrt
from pathlib import Path
from typing import List, Dict, Any
from itertools import groupby

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
            
        logger.info(f"Splitting multi-line subtitles and batching {len(self.subs)} entries into chunks of {batch_size}.")
        
        # Step 1: Create a flat list of "translation units"
        translation_units = []
        for sub in self.subs:
            lines = sub.text.split('\n')
            for i, line in enumerate(lines):
                translation_units.append({
                    "original_index": sub.index,
                    "sub_index": i,
                    "text": line
                })

        # Step 2: Create batches from the flat list
        batches = [translation_units[i:i + batch_size] for i in range(0, len(translation_units), batch_size)]
        logger.info(f"Successfully created {len(batches)} batches from {len(translation_units)} translation units.")
        return batches

    def reconstruct(self, translated_units: List[Dict[str, Any]]):
        """
        Reconstructs the subtitles by grouping and joining translated units.
        """
        if not self.subs:
            raise ValueError("Subtitles have not been parsed yet. Call parse() first.")
        
        logger.info(f"Reconstructing subtitles from {len(translated_units)} translated units.")

        # Create a dictionary for quick lookup of subtitles by index
        subs_dict = {sub.index: sub for sub in self.subs}

        # Sort units by original_index and then sub_index to ensure correct order
        translated_units.sort(key=lambda x: (x['original_index'], x['sub_index']))

        # Group translated units by their original subtitle index
        for original_index, group in groupby(translated_units, key=lambda x: x['original_index']):
            if original_index in subs_dict:
                # Rejoin the lines for this subtitle
                sorted_lines = [unit['text'] for unit in sorted(list(group), key=lambda x: x['sub_index'])]
                subs_dict[original_index].text = '\n'.join(sorted_lines)
            else:
                logger.warning(f"Found translated units for an unknown original_index: {original_index}")

        # Final check to ensure all original subtitles were processed
        if len(subs_dict) > 0:
             logger.info(f"Successfully reconstructed {len(subs_dict)} subtitles.")

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