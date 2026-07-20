import requests
import shutil
import os
import base64
from pathlib import Path
from config_loader import config
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline

# Configuration from loaded config file
LLM_URL = config.get("llm_url", "http://localhost:8080/v1/chat/completions")
MODEL_NAME = config.get("model_name", "gemma-4-12b")
INPUT_DIR = config.get("input_dir", "./input")
OUTPUT_DIR = config.get("output_dir", "./output")

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

def transcribe_audio_with_whisper(file_path, transcriber):
    """
    Transcribes audio using Whisper pipeline.
    """
    file_path = Path(file_path)
    
    # Process audio
    result = transcriber(
        str(file_path),
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

def summarize_text(text):
    """
    Summarizes and highlights key points using the local llama.cpp server.
    """
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": f"Summarize the following in Markdown format, including key highlights, challenges, and takeaways discussed: {text}"}
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
            return content.strip()
        else:
            print(f"Failed to retrieve summary: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None

def run_pipeline(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR, model_name=MODEL_NAME):
    """
    Full pipeline: Transcribe audio -> Summarize text -> Archive files.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
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
            summary = summarize_text(transcribed_text)
            
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
    
    args = parser.parse_args()
    
    # Overwrite globals for LLM configuration
    LLM_URL = args.llm_url
    MODEL_NAME = args.model_name
    
    run_pipeline(input_dir=args.input, output_dir=args.output, model_name=args.model_name)

