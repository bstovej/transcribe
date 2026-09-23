import requests
import shutil
import os
import base64
import re
from datetime import datetime
from pathlib import Path
from config_loader import config
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline

# Configuration from loaded config file
LLM_URL = config.get("llm_url", "http://localhost:8080/v1/chat/completions")
MODEL_NAME = config.get("model_name", "gemma-4-12b")
INPUT_DIR = config.get("input_dir", "./input")
OUTPUT_DIR = config.get("output_dir", "./output")
DEFAULT_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tp_header.md"
TEMPLATE_PATH = config.get("template_path", str(DEFAULT_TEMPLATE_PATH))

def load_whisper_model():
    """
    Load Whisper model and processor for audio transcription from local cache.
    Downloads if not available.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    model_name = "openai/whisper-small"  # Use tiny model for faster local processing, small for quality
    local_model_dir = os.path.join(os.path.expanduser("~"), ".cache", "whisper", model_name)
    
    # Download model if not cached
    print(f"Loading Whisper model from: {local_model_dir}")
    if not os.path.exists(local_model_dir):
        print("Downloading model for offline use...")
        from huggingface_hub import snapshot_download
        snapshot_download(repo_id=model_name, local_dir=local_model_dir)
    
    # Load from local cache
    transcriber = pipeline(
        "automatic-speech-recognition",
        model=local_model_dir,
        device=device,
        return_timestamps=True
    )
    
    return transcriber

def load_audio_file(file_path, sampling_rate=16000):
    """
    Decodes audio file directly using FFmpeg to avoid pipe/stream demuxing issues
    which commonly fail on unoptimized M4A/MP4 containers with metadata at the end.
    """
    import subprocess
    import numpy as np

    ffmpeg_command = [
        "ffmpeg",
        "-i",
        str(file_path),
        "-ac",
        "1",
        "-ar",
        str(sampling_rate),
        "-f",
        "f32le",
        "-hide_banner",
        "-loglevel",
        "quiet",
        "pipe:1",
    ]
    
    try:
        with subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE) as ffmpeg_process:
            out_bytes = ffmpeg_process.communicate()[0]
        
        audio = np.frombuffer(out_bytes, np.float32)
        if audio.shape[0] == 0:
            raise ValueError("FFmpeg output is empty.")
        return audio
    except Exception as e:
        raise RuntimeError(f"Failed to decode audio file via FFmpeg: {e}")

def transcribe_audio_with_whisper(file_path, transcriber):
    """
    Transcribes audio using Whisper pipeline.
    """
    file_path = Path(file_path)
    
    # Load audio into a numpy array first to bypass transformers' stdin/pipe demuxing issues
    audio_data = load_audio_file(file_path)
    
    # Process audio
    result = transcriber(
        audio_data,
        chunk_length_s=30,
        batch_size=16,
        return_timestamps=True
    )
    
    return result.get("text", "").strip()

def translate_text(text):
    """
    Translates text using the local LLM server.
    """
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": f"Translate the following text to English. Output only the translation, nothing else: {text}"}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(LLM_URL, json=payload)
        response.raise_for_status()
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip()
        else:
            print(f"Failed to retrieve translation: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error calling LLM API for translation: {e}")
        return None

def render_frontmatter_template(template_path=None, title=None, source=None):
    """
    Loads YAML frontmatter template from file and renders template variables:
    {{date}}, {{time}}, {{time:FORMAT}}, {{date:FORMAT}}, {{title}}, {{source}}.
    """
    path = Path(template_path) if template_path else Path(TEMPLATE_PATH)
    if not path.exists():
        fallback = Path("templates") / "tp_header.md"
        if fallback.exists():
            path = fallback
        else:
            print(f"Warning: Frontmatter template not found at {path}")
            return ""

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading frontmatter template {path}: {e}")
        return ""

    now = datetime.now()

    def replace_moment_tokens(fmt_str, default_fmt):
        if not fmt_str:
            return now.strftime(default_fmt)
        token_map = [
            ("YYYY", "%Y"),
            ("YY", "%y"),
            ("MM", "%m"),
            ("DD", "%d"),
            ("HH", "%H"),
            ("hh", "%I"),
            ("mm", "%M"),
            ("ss", "%S"),
        ]
        res = fmt_str
        for m_tok, p_tok in token_map:
            res = res.replace(m_tok, p_tok)
        return now.strftime(res)

    def _replace_tag(match):
        tag_type = match.group(1)
        fmt = match.group(2)
        if tag_type == "date":
            return replace_moment_tokens(fmt, "%Y-%m-%d")
        elif tag_type == "time":
            return replace_moment_tokens(fmt, "%H:%M")
        return match.group(0)

    content = re.sub(r"\{\{(date|time)(?::([^}]+))?\}\}", _replace_tag, content)

    if title is not None:
        content = content.replace("{{title}}", str(title))
    if source is not None:
        content = content.replace("{{source}}", str(source))

    return content.strip()

def strip_existing_frontmatter(text):
    """
    Strips existing YAML frontmatter from text if present to avoid duplicate headers.
    """
    stripped = text.strip()
    if stripped.startswith("---"):
        parts = stripped.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return stripped

def prepend_frontmatter(text, template_path=None, title=None, source=None):
    """
    Prepends rendered YAML frontmatter to the given markdown text.
    """
    frontmatter = render_frontmatter_template(template_path=template_path, title=title, source=source)
    if not frontmatter:
        return text
    clean_text = strip_existing_frontmatter(text)
    return f"{frontmatter}\n\n{clean_text}\n"

def summarize_text(text, template_path=None, title=None, source=None):
    """
    Summarizes and highlights key points using the local llama.cpp server.
    """
    prompt = (
        "Summarize the following in Markdown format, including key highlights, challenges, and takeaways discussed. "
        f"Do not use any emojis in the output: {text}"
    )
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(LLM_URL, json=payload)
        response.raise_for_status()
        
        if response.status_code == 200:
            # Handle OpenAI-compatible response from llama.cpp server
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            summary = content.strip()
            return prepend_frontmatter(summary, template_path=template_path, title=title, source=source)
        else:
            print(f"Failed to retrieve summary: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None

def run_pipeline(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR, model_name=MODEL_NAME, template_path=None):
    """
    Full pipeline: Transcribe audio -> Summarize text -> Archive files.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    active_template = template_path or TEMPLATE_PATH
    
    if not input_path.exists():
        print(f"Input path {input_dir} does not exist.")
        return

    if input_path.is_file():
        files_to_process = [input_path]
        archive_dir = input_path.parent / "transcribed-audio"
    else:
        files_to_process = list(input_path.iterdir())
        archive_dir = input_path / "transcribed-audio"
    
    # Ensure directories exist
    output_path.mkdir(exist_ok=True)
    archive_dir.mkdir(exist_ok=True)

    # Supported extensions
    supported_exts = {".mp3", ".m4a", ".wav", ".mp4", ".mpeg", ".mpga", ".webm"}

    # Load Whisper model
    print("Loading Whisper model...")
    transcriber = load_whisper_model()
    print(f"Whisper model loaded: {model_name}")

    # Process files
    for file_path in files_to_process:
        if not file_path.is_file() or file_path.suffix.lower() not in supported_exts:
            continue

        print(f"\n--- Processing: {file_path.name} ---")
        
        try:
            # Step 1: Transcribe
            print("Transcribing with Whisper...")
            transcribed_text = transcribe_audio_with_whisper(file_path, transcriber)
            
            # Save intermediate transcription
            temp_txt_path = file_path.with_name(f"{file_path.stem}-transcribed.txt")
            with open(temp_txt_path, "w", encoding="utf-8") as f:
                f.write(transcribed_text)
            print(f"Transcription saved temporarily to {temp_txt_path.name}")

            # Step 2: Translate (if not already in English)
            if transcribed_text.strip():
                translated_text = translate_text(transcribed_text)
                if translated_text:
                    transcribed_text = translated_text
                    print("Translation completed.")
                else:
                    print("Could not translate, using original text.")
            else:
                print("Transcription is empty, skipping summary.")
            
            # Step 3: Summarize
            print("Summarizing using local LLM...")
            summary = summarize_text(
                transcribed_text,
                template_path=active_template,
                title=file_path.stem,
                source=file_path.name
            )
            
            if summary:
                summary_file = output_path / f"{file_path.stem}-summarized.md"
                with open(summary_file, "w", encoding="utf-8") as f:
                    f.write(summary)
                print(f"Summary saved to {summary_file.name}")
        
            # Step 3: Archive
            print("Archiving original audio/video file...")
            shutil.move(str(file_path), str(archive_dir / file_path.name))
            print(f"Moved original file to {archive_dir}")

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Full transcription and summarization pipeline.")
    parser.add_argument("--input", "-i", default=INPUT_DIR, help="Input directory or single audio/video file")
    parser.add_argument("--output", "-o", default=OUTPUT_DIR, help="Output directory for summaries")
    parser.add_argument("--llm-url", "-u", default=LLM_URL, help="LLM API URL (OpenAI-compatible)")
    parser.add_argument("--model-name", "-m", default=MODEL_NAME, help="Model name for local LLM")
    parser.add_argument("--template", "-t", default=str(TEMPLATE_PATH), help="Frontmatter template markdown file path")
    
    args = parser.parse_args()
    
    # Overwrite globals for LLM configuration
    LLM_URL = args.llm_url
    MODEL_NAME = args.model_name
    
    run_pipeline(
        input_dir=args.input,
        output_dir=args.output,
        model_name=args.model_name,
        template_path=args.template
    )

