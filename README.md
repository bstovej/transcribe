# Transcribe and Summarize

This project provides a set of Python scripts for batch transcribing audio files and summarizing the transcriptions using:
- **Whisper** for speech-to-text transcription (offline-capable, runs locally)
- **Local LLMs via llama.cpp server or Ollama** for translation, summarization, text enhancement, and multimodal transcription (OpenAI-compatible API, e.g. Gemma-4-12b, Qwen3.5, etc.)

Now includes a **Docker-based environment** and a **Web Dashboard** for easier management.

## ⚡ Performance Tips
- **GPU acceleration**: Install PyTorch with CUDA for 10-50x faster transcription
- **Model selection**: Use `whisper-tiny` (fast, ~40MB), `whisper-base` (balanced), or `whisper-small` (quality)
- **Batch processing**: Process multiple files in sequence without reloading models

---

## 🚀 Getting Started with Docker (Recommended)

The easiest way to run the project is using Docker and Docker Compose. This ensures all dependencies like `ffmpeg` and Python libraries are correctly configured.

### Prerequisites
1.  **Docker & Docker Compose** installed.
2.  **Python + PyTorch + Transformers** installed on your host.
3.  **Local LLM server** running on your host machine with OpenAI-compatible API support:
    *   **llama.cpp server**: e.g., `./llama-server -hf unsloth/gemma-4-12b-it-GGUF:UD-Q4_K_XL --port 8080` (requires multimodal audio support if running `transcribe_only.py`).
    *   **Ollama**: e.g., `ollama run qwen3.5:9b` (OpenAI-compatible endpoint at `http://host.docker.internal:11434/v1/chat/completions` or `http://localhost:11434/v1/chat/completions`).
    *   Ensure the server is accessible from Docker (default config uses `host.docker.internal`).
4.  **Whisper Model Cache**: The script will download the Whisper model on first run and cache it locally at `~/.cache/whisper/openai/whisper-small` for offline use.

### 1. Clone the Repository
```bash
git clone https://github.com/bstovej/transcribe.git
cd transcribe
```

### 2. Configuration
Create your configuration file by copying the sample config:
```bash
cp sample_transcribe_config.json transcribe_config.json
```

Then update `transcribe_config.json` with your local settings:
*   `llm_url`: The OpenAI-compatible API endpoint for translation/summarization or multimodal transcription (e.g., `http://host.docker.internal:8080/v1/chat/completions` or `http://localhost:11434/v1/chat/completions`).
*   `model_name`: The language/multimodal model name (e.g., `gemma-4-12b` or `qwen3.5:9b`).
*   `input_dir`: Path to source audio/video files (default: `./input`).
*   `output_dir`: Path to destination folder for transcriptions and summaries (default: `./output`).
*   `template_path`: Path to a Markdown template file for YAML frontmatter (default: `./templates/tp_header.md`).

#### Frontmatter Templating
Summaries prepend customizable YAML frontmatter rendered from the template specified by `template_path`. The template supports dynamic placeholder tokens:
*   `{{date}}`: Current date (`YYYY-MM-DD` by default, or customized via `{{date:FORMAT}}` e.g. `{{date:YYYY/MM/DD}}`).
*   `{{time}}`: Current time (`HH:mm` by default, or customized via `{{time:FORMAT}}` e.g. `{{time:YYYY-MM-DDTHH:mm}}`).
*   `{{title}}`: Stem / base filename of the processed file.
*   `{{source}}`: Full filename of the processed source file.

Existing frontmatter headers are automatically stripped before prepending to prevent duplicate metadata.

### 3. Build and Run the Web UI
Launch the Flask dashboard to manage tasks visually:
```bash
docker-compose build
docker-compose up ui
```
**Security Note:** For your protection, the UI is bound to `127.0.0.1`. It is **only** accessible from your local machine at: **http://localhost:8501**

### 4. API Integration
The system exposes a REST API for external applications:
- **Upload & Transcribe:** `POST http://<server-ip>:8501/api/upload` (multipart/form-data with `file`)
  - Returns `{"job_id": "<uuid>"}`
- **Check Status:** `GET http://<server-ip>:8501/api/status/<job_id>`
  - Returns current processing status and results when completed.

### 5. Run Specific Scripts via CLI
You can also run specific tasks directly from the terminal using Docker Compose:

*   **Full Pipeline** (Whisper Transcribe → LLM Translate → LLM Summarize with Frontmatter):
    ```bash
    docker-compose run transcribe
    ```
*   **Transcribe Only** (via multimodal LLM API):
    ```bash
    docker-compose run transcribe_only
    ```
*   **Summarize / Enhance Only** (for existing transcriptions):
    ```bash
    docker-compose run summarize
    ```

---

## 🛠️ Local Setup (Without Docker)

If you prefer to run scripts directly on your host:

### Prerequisites
1.  **Python 3.10+**
2.  **PyTorch** with CUDA support (for faster processing): `pip install torch --index-url https://download.pytorch.org/whl/cu121`
3.  **Transformers** library: `pip install transformers torch`
4.  **FFmpeg** installed on your system (used for audio decoding).
5.  **Local LLM Server**: **llama.cpp server** or **Ollama** running locally with an OpenAI-compatible endpoint enabled.

### 1. Clone the Repository
```bash
git clone https://github.com/bstovej/transcribe.git
cd transcribe
```

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Configuration
Create and edit your configuration file:
```bash
cp sample_transcribe_config.json transcribe_config.json
```
Customize `input_dir`, `output_dir`, `llm_url`, `model_name`, and `template_path` to match your local paths and server configuration.

### 4. Usage
#### 1. Full Pipeline (`transcribe.py`)
Transcribes audio using local Whisper, translates if needed via LLM, generates a structured markdown summary with YAML frontmatter, and archives the original audio file.

```bash
python transcribe.py
```

Override configuration settings directly via CLI arguments, or pass a single file instead of a folder:
```bash
python transcribe.py --input /path/to/recording.mp3 --output /path/to/output --llm-url http://localhost:8080/v1/chat/completions --model-name gemma-4-12b --template templates/tp_header.md
```

**Options for `transcribe.py`:**
*   `-i`, `--input`: Input directory path or path to a single audio/video file (`.mp3`, `.m4a`, `.wav`, `.mp4`, `.mpeg`, `.mpga`, `.webm`).
*   `-o`, `--output`: Destination directory for Markdown summaries.
*   `-u`, `--llm-url`: OpenAI-compatible API endpoint URL for translation and summarization.
*   `-m`, `--model-name`: Model name to supply in LLM API requests.
*   `-t`, `--template`: Path to the YAML frontmatter template markdown file.

#### 2. Summarize & Enhance Existing Transcripts (`summarize_text.py`)
Processes existing `*-transcribed.txt` files (or a single transcription file) to summarize or enhance readability, prepending YAML frontmatter.

```bash
# Summarize transcriptions (default)
python summarize_text.py --action summarize

# Enhance grammar and readability
python summarize_text.py --action enhance
```

**Options for `summarize_text.py`:**
*   `--action`: `summarize` (default) or `enhance`.
*   `-i`, `--input`: Input directory containing `*-transcribed.txt` files or path to a single text file.
*   `-o`, `--output`: Output directory where summaries (`*-summarized.md`) or enhancements (`*-enhanced.md`) are written.
*   `-u`, `--llm-url`: OpenAI-compatible API endpoint URL.
*   `-m`, `--model-name`: LLM model name.
*   `-t`, `--template`: Path to YAML frontmatter template.

#### 3. Transcribe Only via Multimodal LLM (`transcribe_only.py`)
Transcribes audio directly using a multimodal LLM endpoint (`input_audio` format), saving `*-transcribed.txt` alongside the source file and archiving the media file.

```bash
python transcribe_only.py --input /path/to/recording.mp3 --llm-url http://localhost:8080/v1/chat/completions --model-name qwen3.5:9b
```

**Options for `transcribe_only.py`:**
*   `-i`, `--input`: Input directory or path to a single audio/video file.
*   `-u`, `--llm-url`: Multimodal OpenAI-compatible API endpoint URL.
*   `-m`, `--model-name`: Model name to supply in LLM API requests.

### Offline Mode
For `transcribe.py`, the Whisper model (`openai/whisper-small`) is downloaded on first run and cached locally at `~/.cache/whisper/openai/whisper-small`. Audio streams are decoded directly via FFmpeg into memory, bypassing standard demuxing issues with M4A/MP4 containers. After the initial model download, Whisper transcription operates completely offline.

### GPU Acceleration
For faster Whisper transcription, install PyTorch with CUDA support and verify your GPU device:
```python
import torch
print(torch.cuda.is_available())  # Should return True
```

---

## 📁 Project Structure
- `sample_transcribe_config.json`: Template configuration file.
- `transcribe_config.json`: Local active configuration (ignored by Git).
- `input/`: Source audio/video files.
  - `transcribed-audio/`: Archive of processed audio/video files.
- `output/`: Final Markdown summaries (`*-summarized.md`) and enhanced transcripts (`*-enhanced.md`).
- `templates/`: Templates directory, including `tp_header.md` (YAML frontmatter template) and `index.html` (Web UI).
- `static/`: Frontend scripts (`app.js`) and styles (`style.css`).
- `app.py`: Flask Web Dashboard & API Server.
- `job_manager.py`: Manages the single-worker task queue.
- `api_processing.py`: Handles single-file API transcription requests.
- `transcribe.py`: Full pipeline: Local Whisper Transcribe → LLM Translate → LLM Summarize with Frontmatter.
- `transcribe_only.py`: Multimodal LLM audio transcription utility.
- `summarize_text.py`: Batch summarization and text enhancement with frontmatter templating.
- `config_loader.py`: Central loader for configuration settings with fallback defaults.

## 🎯 Pipeline Overview
1. **Transcribe**: Audio/video → Whisper (`transcribe.py`) or Multimodal LLM (`transcribe_only.py`) → Text (`*-transcribed.txt`)
2. **Translate**: Text (if non-English) → LLM → English text
3. **Summarize / Enhance**: English text → LLM → Structured Markdown summary (`*-summarized.md`) or enhanced text (`*-enhanced.md`)
4. **Frontmatter Header**: Template variables (`{{date}}`, `{{time}}`, `{{title}}`, `{{source}}`) rendered and prepended to output
5. **Archive**: Original audio/video files moved to `transcribed-audio/`

