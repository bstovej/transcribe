import shutil
import os
import requests
import base64
from pathlib import Path
from config_loader import config

LLM_URL = config.get("llm_url", "http://localhost:8080/v1/chat/completions")
MODEL_NAME = config.get("model_name", "gpt-3.5-turbo")
INPUT_DIR = config.get("input_dir", "./input")

def transcribe_audio_via_llm(file_path):
    """
    Transcribes audio using the multimodal local LLM endpoint.
    """
    file_path = Path(file_path)
    
    with open(file_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    format_ext = file_path.suffix.lower()[1:]
    if format_ext == "m4a": 
        format_ext = "mp4"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_b64,
                            "format": format_ext
                        }
                    },
                    {
                        "type": "text",
                        "text": "Please transcribe this audio exactly word-for-word. Do not output anything other than the transcription."
                    }
                ]
            }
        ],
        "stream": False
    }
    
    response = requests.post(LLM_URL, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

def transcribe_files(input_dir=INPUT_DIR):
    """
    Transcribes all audio files in the specified directory and moves them to an archive.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Path {input_dir} does not exist.")
        return

    if input_path.is_file():
        files_to_process = [input_path]
        archive_dir = input_path.parent / "transcribed-audio"
    else:
        files_to_process = list(input_path.iterdir())
        archive_dir = input_path / "transcribed-audio"

    # Ensure archive directory exists
    archive_dir.mkdir(exist_ok=True)

    # Supported extensions
    supported_exts = {".mp3", ".m4a", ".wav", ".mp4", ".mpeg", ".mpga", ".webm"}

    # Iterate over files in the input directory
    for file_path in files_to_process:
        # Skip directories and non-audio files
        if not file_path.is_file() or file_path.suffix.lower() not in supported_exts:
            continue

        print(f"Transcribing {file_path.name} via LLM...")
        try:
            # Step 1: Transcribe
            raw_text = transcribe_audio_via_llm(file_path)

            # Step 2: Save transcription next to original file
            output_text_file = file_path.with_name(f"{file_path.stem}-transcribed.txt")
            with open(output_text_file, "w", encoding="utf-8") as text_file:
                text_file.write(raw_text)
            
            print(f"Transcription saved to {output_text_file.name}")

            # Step 3: Move only the original audio/video file to the archive folder
            dest_audio = archive_dir / file_path.name
            
            shutil.move(str(file_path), str(dest_audio))
            
            print(f"Moved original file to {archive_dir}")

        except Exception as e:
            print(f"An error occurred processing {file_path.name}: {e}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Transcription only script.")
    parser.add_argument("--input", "-i", default=INPUT_DIR, help="Input directory or single audio/video file")
    parser.add_argument("--llm-url", "-u", default=LLM_URL, help="LLM API URL (OpenAI-compatible)")
    parser.add_argument("--model-name", "-m", default=MODEL_NAME, help="Model name for local LLM")
    
    args = parser.parse_args()
    
    # Overwrite globals for LLM configuration
    LLM_URL = args.llm_url
    MODEL_NAME = args.model_name
    
    transcribe_files(args.input)
