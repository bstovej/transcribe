# Transcribe and Summarize

This project provides a set of Python scripts for batch transcribing audio files and summarizing the transcriptions using:
- **Whisper** for speech-to-text transcription (offline-capable, runs locally)
- **llama.cpp server** for translation and summarization (OpenAI-compatible API, e.g. Gemma-4-12b)

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
3.  **llama.cpp server** running on your host machine with multimodal (audio) support.
    *   Start the server with the OpenAI API enabled: `./llama-server -hf unsloth/gemma-4-12b-it-GGUF:UD-Q4_K_XL --port 8080`
    *   Ensure the server is accessible from Docker (default config uses `host.docker.internal`).
4.  **Whisper Model Cache**: The script will download Whisper model on first run and cache it locally at `~/.cache/whisper/openai/whisper-tiny` for offline use.

### 1. Configuration
Settings are managed in `transcribe_config.json`. You can modify this file to change:
*   `llm_url`: The OpenAI-compatible API endpoint for translation/summarization (e.g., `http://host.docker.internal:8080/v1/chat/completions`).
*   `model_name`: The language model name (e.g., `gemma-4-12b`).
*   `input_dir`: Source folder for audio files (default: `./input`).
*   `output_dir`: Destination folder for transcriptions/summaries (default: `./output`).
*   `whisper_model`: Optional - Whisper model to use (default: `openai/whisper-tiny`). Use `openai/whisper-base` or `openai/whisper-small` for better quality.

### 2. Build and Run the Web UI
Launch the Flask dashboard to manage tasks visually:
```bash
docker-compose build
docker-compose up ui
```
**Security Note:** For your protection, the UI is bound to `127.0.0.1`. It is **only** accessible from your local machine at: **http://localhost:8501**

### 3. API Integration
The system now exposes a robust API for external applications:
- **Upload & Transcribe:** `POST http://<server-ip>:8501/api/upload` (multipart/form-data with `file`)
  - Returns `{"job_id": "<uuid>"}`
- **Check Status:** `GET http://<server-ip>:8501/api/status/<job_id>`
  - Returns current processing status and results when completed.

### 3. Run Specific Scripts via CLI
You can also run specific tasks directly from the terminal using Docker Compose:

*   **Full Pipeline** (Transcribe → Translate → Summarize):
    ```bash
    docker-compose run transcribe
    ```
*   **Transcribe Only**:
    ```bash
    docker-compose run transcribe_only
    ```
*   **Summarize Only** (for existing transcriptions):
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
4.  **FFmpeg** installed on your system.
5.  **llama.cpp server** running locally.

### Installation
```bash
pip install -r requirements.txt
```

### Usage
Run the pipeline using Python:
```bash
python transcribe.py
```
By default, the script loads settings from `transcribe_config.json`.

#### Overriding Configuration via CLI Arguments
You can override configuration settings directly via command line arguments. This also enables processing a single audio/video file directly instead of an entire folder:

```bash
python transcribe.py --input /path/to/audio_file.mp3 --output /path/to/output_dir --llm-url http://localhost:8080/v1/chat/completions --model-name my-custom-model
```

**Available Options:**
*   `-i`, `--input`: Input directory path or path to a single audio/video file (e.g. `.mp3`, `.m4a`, `.wav`, etc.).
*   `-o`, `--output`: Output directory where Markdown summaries will be written.
*   `-u`, `--llm-url`: OpenAI-compatible API endpoint URL for translation/summarization.
*   `-m`, `--model-name`: Model name to supply in the LLM API payload.

The scripts will automatically fall back to settings from `transcribe_config.json` if arguments are omitted.

### Offline Mode
The Whisper model is downloaded on the first run and cached at `~/.cache/whisper/`. To avoid any network round-trips or metadata checks to Hugging Face Hub (which can issue warnings or rate limits), the script loads directly using the local filesystem path. After the initial download, transcription is fully offline and requires no internet access.

### GPU Acceleration
For faster transcription, install PyTorch with CUDA and ensure your GPU is recognized:
```python
# Check device
import torch
print(torch.cuda.is_available())  # Should return True
```

---

## 📁 Project Structure
- `input/`: Place your source audio files here.
- `output/`: Generated transcriptions (`*-transcribed.txt`) and summaries (`*-summarized.md`).
- `transcribe_config.json`: Central configuration file.
- `app.py`: Flask Web Dashboard & API Server.
- `job_manager.py`: Manages the single-worker task queue.
- `api_processing.py`: Handles single-file API transcription requests.
- `transcribe.py`: Full pipeline: Transcribe (Whisper) → Translate → Summarize.
- `transcribe_only.py`: Only performs Whisper transcription (batch).
- `summarize_text.py`: Generates summaries from transcriptions (batch).
- `templates/` & `static/`: Web UI components.

## 🎯 Pipeline Overview
1. **Transcribe**: Audio files → Whisper → Text (`*-transcribed.txt`)
2. **Translate**: Text (if needed) → LLM → English text
3. **Summarize**: English text → LLM → Markdown summary (`*-summarized.md`)
4. **Archive**: Original files moved to `input/transcribed-audio/`
