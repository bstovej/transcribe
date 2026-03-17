import requests
import os
from pathlib import Path
from config_loader import config

OLLAMA_URL = config.get("ollama_url", "http://localhost:11434/api/chat")
MODEL_NAME = config.get("model_name", "llama3.2:latest")
INPUT_DIR = config.get("input_dir", "./input")
OUTPUT_DIR = config.get("output_dir", "./output")

def enhance_text(text):
    """
    Summarizes and highlights key points using the local Ollama LLM.
    """
    payload = {
        "messages": [
            {"role": "user", "content": f"Summarize the following in Markdown format, including key highlights, challenges, and takeaways discussed: {text}"}
        ],
        "stream": False,
        "model": MODEL_NAME
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        
        if response.status_code == 200:
            content = response.json().get("message", {}).get("content", "")
            return content.strip()
        else:
            print(f"Failed to retrieve results: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error calling Ollama API: {e}")
        return None

def process_transcriptions(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR):
    """
    Reads transcribed files from input_dir and saves enhanced summaries to output_dir.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    if not input_path.exists():
        print(f"Input directory {input_dir} does not exist.")
        return

    # Find all -transcribed.txt files
    transcribed_files = list(input_path.glob("*-transcribed.txt"))
    
    if not transcribed_files:
        print(f"No transcribed files found in {input_dir}.")
        return

    print(f"Found {len(transcribed_files)} files to process.")

    for file_path in transcribed_files:
        print(f"Processing {file_path.name}...")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            if not text.strip():
                print(f"Skipping empty file: {file_path.name}")
                continue

            summary = enhance_text(text)
            
            if summary:
                # Save to output folder with a -enhanced.md suffix
                output_file = output_path / file_path.name.replace("-transcribed.txt", "-enhanced.md")
                
                with open(output_file, "w", encoding="utf-8") as out_f:
                    out_f.write(summary)
                
                print(f"Summary saved to {output_file.name}")
            else:
                print(f"Failed to generate summary for {file_path.name}")

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    process_transcriptions()
