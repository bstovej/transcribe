import whisper
import requests
import shutil
import os
from pathlib import Path
from config_loader import config

# Configuration from loaded config file
LLM_URL = config.get("llm_url", "http://localhost:8080/v1/chat/completions")
MODEL_NAME = config.get("model_name", "gpt-3.5-turbo")
WHISPER_MODEL = config.get("whisper_model", "base")
INPUT_DIR = config.get("input_dir", "./input")
OUTPUT_DIR = config.get("output_dir", "./output")

def summarize_text(text):
    """
    Summarizes and highlights key points using the local llama.cpp server.
    """
    payload = {
        "messages": [
            {"role": "user", "content": f"Summarize the following in Markdown format, including key highlights, challenges, and takeaways discussed: {text}"}
        ],
        "stream": False,
        "model": MODEL_NAME
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

def run_pipeline(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR, model_name=WHISPER_MODEL):
    """
    Full pipeline: Transcribe audio -> Summarize text -> Archive files.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    archive_dir = input_path / "transcribed-audio"
    
    # Ensure directories exist
    output_path.mkdir(exist_ok=True)
    archive_dir.mkdir(exist_ok=True)

    if not input_path.exists():
        print(f"Input directory {input_dir} does not exist.")
        return

    # Whisper-supported extensions
    supported_exts = {".mp3", ".m4a", ".wav", ".mp4", ".mpeg", ".mpga", ".webm"}

    print(f"Loading Whisper model '{model_name}'...")
    try:
        model = whisper.load_model(model_name)
    except Exception as e:
        print(f"Failed to load Whisper model: {e}")
        return

    # Process files
    for file_path in input_path.iterdir():
        if not file_path.is_file() or file_path.suffix.lower() not in supported_exts:
            continue

        print(f"\n--- Processing: {file_path.name} ---")
        
        try:
            # Step 1: Transcribe
            print("Transcribing...")
            result = model.transcribe(str(file_path))
            transcribed_text = result["text"]
            
            # Save intermediate transcription
            temp_txt_path = file_path.with_name(f"{file_path.stem}-transcribed.txt")
            with open(temp_txt_path, "w", encoding="utf-8") as f:
                f.write(transcribed_text)
            print(f"Transcription saved temporarily to {temp_txt_path.name}")

            # Step 2: Summarize
            if transcribed_text.strip():
                print("Summarizing using local LLM...")
                summary = summarize_text(transcribed_text)
                
                if summary:
                    summary_file = output_path / f"{file_path.stem}-summarized.md"
                    with open(summary_file, "w", encoding="utf-8") as f:
                        f.write(summary)
                    print(f"Summary saved to {summary_file}")
                else:
                    print("Could not generate summary.")
            else:
                print("Transcription is empty, skipping summary.")

            # Step 3: Archive
            print("Archiving original audio/video file...")
            shutil.move(str(file_path), str(archive_dir / file_path.name))
            print(f"Moved original file to {archive_dir}")

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

if __name__ == '__main__':
    run_pipeline()
