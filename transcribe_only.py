import whisper
import shutil
import os
from pathlib import Path
from config_loader import config

WHISPER_MODEL = config.get("whisper_model", "base")
INPUT_DIR = config.get("input_dir", "./input")

def transcribe_files(input_dir=INPUT_DIR, model_name=WHISPER_MODEL):
    """
    Transcribes all audio files in the specified directory and moves them to an archive.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Directory {input_dir} does not exist.")
        return

    # Ensure archive directory exists
    archive_dir = input_path / "transcribed-audio"
    archive_dir.mkdir(exist_ok=True)

    # Whisper-supported extensions
    supported_exts = {".mp3", ".m4a", ".wav", ".mp4", ".mpeg", ".mpga", ".webm"}

    print(f"Loading Whisper model '{model_name}'...")
    try:
        model = whisper.load_model(model_name)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # Iterate over files in the input directory
    for file_path in input_path.iterdir():
        # Skip directories and non-audio files
        if not file_path.is_file() or file_path.suffix.lower() not in supported_exts:
            continue

        print(f"Transcribing {file_path.name}...")
        try:
            # Step 1: Transcribe
            result = model.transcribe(str(file_path))
            raw_text = result["text"]

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
    # Use config-loaded directory
    transcribe_files(INPUT_DIR)
