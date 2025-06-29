import re
from pathlib import Path
from typing import List, NamedTuple, Callable, Optional

from openai import OpenAI
from app.core.config import settings

# --- Constants ---
# A separator that is unlikely to appear in subtitle text
BATCH_SEPARATOR = "|||---|||"
# A rough estimate of tokens per character for batching
TOKENS_PER_CHAR = 0.5
# Max tokens for a single batch to avoid overwhelming the API
MAX_TOKENS_PER_BATCH = 3000

SYSTEM_PROMPT = """You are an expert subtitle translator. Your task is to translate the given text fragments from a source language into {target_language}.

- You will receive a batch of subtitle texts concatenated by a special separator '|||---|||'.
- Translate each fragment individually.
- Return the translated fragments, preserving the original '|||---|||' separator between each one.
- Do NOT translate the '|||---|||' separator.
- Ensure the translation is accurate, natural, and adheres to the context of subtitles.
- Do not add any extra text, introductory phrases, or explanations. Only return the translated fragments joined by the separator.
- The number of fragments you return must exactly match the number of fragments you receive.
"""

class SubtitleBlock(NamedTuple):
    index: int
    start_time: str
    end_time: str
    text: str


def parse_srt(content: str) -> List[SubtitleBlock]:
    """Parses SRT content into a list of SubtitleBlock objects."""
    content = content.replace('\r\n', '\n').strip()
    blocks = []
    # A more robust regex to handle various line endings and optional trailing newlines
    for match in re.finditer(
        r'(\d+)\n([\d:,]+)\s-->\s([\d:,]+)\n([\s\S]+?)(?=\n\n\d+|\Z)',
        content
    ):
        blocks.append(SubtitleBlock(
            index=int(match.group(1)),
            start_time=match.group(2).replace(',', '.'),
            end_time=match.group(3).replace(',', '.'),
            text=match.group(4).strip()
        ))
    return blocks


def build_srt(blocks: List[SubtitleBlock]) -> str:
    """Builds an SRT content string from a list of SubtitleBlock objects."""
    srt_content = []
    for block in blocks:
        start_time = block.start_time.replace('.', ',')
        end_time = block.end_time.replace('.', ',')
        srt_content.append(
            f"{block.index}\n{start_time} --> {end_time}\n{block.text}\n"
        )
    return "\n".join(srt_content)


def _translate_batch(texts: List[str], target_language: str, model: str, client: OpenAI) -> List[str]:
    """Translates a batch of texts using the LLM."""
    if not texts:
        return []

    concatenated_text = BATCH_SEPARATOR.join(texts)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(target_language=target_language)},
                {"role": "user", "content": concatenated_text},
            ],
            temperature=0.2, # Lower temperature for more deterministic translation
        )
        
        translated_text = response.choices[0].message.content
        if not translated_text:
            raise ValueError("LLM returned an empty response.")
            
        translated_fragments = translated_text.split(BATCH_SEPARATOR)

        if len(translated_fragments) != len(texts):
             raise ValueError(
                f"Translation fragment count mismatch. Expected {len(texts)}, got {len(translated_fragments)}."
            )
            
        return [fragment.strip() for fragment in translated_fragments]

    except Exception as e:
        print(f"An error occurred during translation: {e}")
        # In case of any error, return original texts as a fallback
        return texts


def translate_file(
    source_path: Path, 
    target_language: str, 
    model: str, 
    update_callback: Optional[Callable[[float], None]] = None
) -> Path:
    """
    Reads an SRT file, translates its content using an LLM, and saves it to a new file,
    providing progress updates along the way.
    """
    def _update_progress(progress: float):
        if update_callback:
            update_callback(progress)

    _update_progress(0.0)
    print(f"Starting translation for {source_path.name} to {target_language} using {model}")
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)

    source_content = source_path.read_text(encoding='utf-8')
    subtitle_blocks = parse_srt(source_content)
    
    if not subtitle_blocks:
        raise ValueError("The SRT file is empty or has an invalid format.")

    _update_progress(0.1) # Progress after parsing

    all_texts = [block.text for block in subtitle_blocks]
    translated_texts = []
    
    # Simple batching logic based on token count
    current_batch = []
    current_token_count = 0
    total_texts = len(all_texts)

    for i, text in enumerate(all_texts):
        text_token_count = len(text) * TOKENS_PER_CHAR
        if current_token_count + text_token_count > MAX_TOKENS_PER_BATCH:
            translated_batch = _translate_batch(current_batch, target_language, model, client)
            translated_texts.extend(translated_batch)
            current_batch = [text]
            current_token_count = text_token_count
        else:
            current_batch.append(text)
            current_token_count += text_token_count
        
        # Update progress after processing each text
        progress = 0.1 + ( (i + 1) / total_texts * 0.8 ) # Translation is 80% of the work
        _update_progress(progress)


    # Translate the last remaining batch
    if current_batch:
        translated_batch = _translate_batch(current_batch, target_language, model, client)
        translated_texts.extend(translated_batch)

    if len(translated_texts) != total_texts:
        raise ValueError("Mismatch in translated text count after batching.")

    translated_blocks = [
        block._replace(text=translated_texts[i]) for i, block in enumerate(subtitle_blocks)
    ]

    translated_srt_content = build_srt(translated_blocks)
    _update_progress(0.95) # Progress after building SRT
    
    result_dir = Path(settings.RESULT_FILE_DIR)
    result_dir.mkdir(exist_ok=True)
    result_path = result_dir / f"translated_{source_path.stem}.srt"
    
    result_path.write_text(translated_srt_content, encoding='utf-8')
    
    print(f"Translation finished. Result saved to {result_path}")
    _update_progress(1.0) # Final progress
    
    return result_path 