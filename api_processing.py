import os
from pathlib import Path
from config_loader import config
import transcribe

def process_single_file(file_path, output_dir, summarize=True):
    """
    Transcribes and optionally summarizes a single file.
    """
    file_path = Path(file_path)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    if not file_path.exists():
        print(f"File {file_path} does not exist.")
        return None

    print(f"Transcribing: {file_path.name} via LLM API...")
    transcribed_text = transcribe.transcribe_audio_via_llm(file_path)

    if not transcribed_text.strip():
        print("Transcription is empty.")
        return {"transcription": "", "summary": None}

    summary = None
    if summarize:
        print("Summarizing...")
        summary = transcribe.summarize_text(transcribed_text)
        
        if summary:
            summary_file = output_path / f"{file_path.stem}-api-summary.md"
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"Summary saved to {summary_file.name}")

    return {
        "transcription": transcribed_text,
        "summary": summary
    }
