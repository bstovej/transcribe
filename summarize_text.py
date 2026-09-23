import requests
import os
import re
from datetime import datetime
from pathlib import Path
from config_loader import config

# Configuration from loaded config file
LLM_URL = config.get("llm_url", "http://localhost:8080/v1/chat/completions")
MODEL_NAME = config.get("model_name", "gpt-3.5-turbo")
INPUT_DIR = config.get("input_dir", "./input")
OUTPUT_DIR = config.get("output_dir", "./output")
DEFAULT_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tp_header.md"
TEMPLATE_PATH = config.get("template_path", str(DEFAULT_TEMPLATE_PATH))

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

def summarize_text(text, action="summarize", template_path=None, title=None, source=None):
    """
    Summarizes or enhances text using the local llama.cpp server.
    """
    if action == "enhance":
        prompt = (
            "Enhance the following text, correcting grammar and improving readability without losing the original meaning, "
            f"in Markdown format. Do not use any emojis in the output: {text}"
        )
    else:
        prompt = (
            "Summarize the following in Markdown format, including key highlights, challenges, and takeaways discussed. "
            f"Do not use any emojis in the output: {text}"
        )

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
            summary = content.strip()
            return prepend_frontmatter(summary, template_path=template_path, title=title, source=source)
        else:
            print(f"Failed to retrieve results: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None

def process_transcriptions(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR, action="summarize", template_path=None):
    """
    Reads transcribed files from input_dir and saves processed summaries/enhancements to output_dir.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    active_template = template_path or TEMPLATE_PATH

    if not input_path.exists():
        print(f"Input path {input_dir} does not exist.")
        return

    # Handle single file or directory search
    if input_path.is_file():
        transcribed_files = [input_path]
    else:
        # Find all -transcribed.txt files
        transcribed_files = list(input_path.glob("*-transcribed.txt"))
    
    if not transcribed_files:
        print(f"No transcribed files found at/in {input_dir}.")
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

            title = file_path.stem.replace("-transcribed", "")
            summary = summarize_text(
                text,
                action=action,
                template_path=active_template,
                title=title,
                source=file_path.name
            )
            
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
    parser.add_argument("--input", "-i", default=INPUT_DIR, help="Input directory or single transcription file")
    parser.add_argument("--output", "-o", default=OUTPUT_DIR, help="Output directory for summaries")
    parser.add_argument("--llm-url", "-u", default=LLM_URL, help="LLM API URL (OpenAI-compatible)")
    parser.add_argument("--model-name", "-m", default=MODEL_NAME, help="Model name for local LLM")
    parser.add_argument("--template", "-t", default=str(TEMPLATE_PATH), help="Frontmatter template markdown file path")
    
    args = parser.parse_args()
    
    # Overwrite globals for LLM configuration
    LLM_URL = args.llm_url
    MODEL_NAME = args.model_name
    
    process_transcriptions(
        input_dir=args.input,
        output_dir=args.output,
        action=args.action,
        template_path=args.template
    )
