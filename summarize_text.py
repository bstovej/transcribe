import requests
import os
from pathlib import Path
from config_loader import config

# Configuration from loaded config file
LLM_URL = config.get("llm_url", "http://localhost:8080/v1/chat/completions")
MODEL_NAME = config.get("model_name", "gpt-3.5-turbo")
INPUT_DIR = config.get("input_dir", "./input")
OUTPUT_DIR = config.get("output_dir", "./output")

def summarize_text(text, action="summarize"):
    """
    Summarizes or enhances text using the local llama.cpp server.
    """
    if action == "enhance":
        prompt = f"Enhance the following text, correcting grammar and improving readability without losing the original meaning, in Markdown format: {text}"
    else:
        prompt = f"Summarize the following in Markdown format, including key highlights, challenges, and takeaways discussed: {text}"

    payload = {
        "messages": [
            {"role": "user", "content": prompt}
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
            print(f"Failed to retrieve results: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None

def process_transcriptions(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR, action="summarize"):
    """
    Reads transcribed files from input_dir and saves processed summaries/enhancements to output_dir.
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

    print(f"Found {len(transcribed_files)} files to process for action: {action}.")

    for file_path in transcribed_files:
        print(f"Processing {file_path.name}...")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            if not text.strip():
                print(f"Skipping empty file: {file_path.name}")
                continue

            summary = summarize_text(text, action=action)
            
            if summary:
                # Save to output folder with the appropriate suffix
                suffix = "-enhanced.md" if action == "enhance" else "-summarized.md"
                output_file = output_path / file_path.name.replace("-transcribed.txt", suffix)
                
                with open(output_file, "w", encoding="utf-8") as out_f:
                    out_f.write(summary)
                
                print(f"Result saved to {output_file.name}")
            else:
                print(f"Failed to process {file_path.name}")

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process transcriptions.")
    parser.add_argument("--action", choices=["summarize", "enhance"], default="summarize", help="Action to perform")
    args = parser.parse_args()
    process_transcriptions(action=args.action)
