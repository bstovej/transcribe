# Transcribe and Summarize

This project provides a set of Python scripts for batch transcribing audio files using OpenAI's Whisper model and summarizing the transcriptions using a local LLM via a **llama.cpp server** (OpenAI-compatible API). 

Now includes a **Docker-based environment** and a **Web Dashboard** for easier management.

---

## 🚀 Getting Started with Docker (Recommended)

The easiest way to run the project is using Docker and Docker Compose. This ensures all dependencies like `ffmpeg` and Python libraries are correctly configured.

### Prerequisites
1.  **Docker & Docker Compose** installed.
2.  **llama.cpp server** running on your host machine.
    *   Start the server with the OpenAI API enabled: `./llama-server -m your_model.gguf --port 8080`
    *   Ensure the server is accessible from Docker (default config uses `host.docker.internal`).

### 1. Configuration
Settings are managed in `transcribe_config.json`. You can modify this file to change:
*   `llm_url`: The OpenAI-compatible API endpoint (e.g., `http://host.docker.internal:8080/v1/chat/completions`).
*   `model_name`: The model name to pass in the request (llama.cpp often ignores this).
*   `whisper_model`: The Whisper model size (`tiny`, `base`, `small`, `medium`, `large`).
*   `input_dir` & `output_dir`: Folder paths inside the container.

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

*   **Full Pipeline** (Transcribe + Summarize):
    ```bash
    docker-compose run transcribe
    ```
*   **Transcribe Only**:
    ```bash
    docker-compose run transcribe_only
    ```
*   **Summarize Only**:
    ```bash
    docker-compose run summarize
    ```

---

## 🛠️ Local Setup (Without Docker)

If you prefer to run scripts directly on your host:

### Prerequisites
1.  **Python 3.10+**
2.  **FFmpeg** installed on your system.
3.  **llama.cpp server** running locally.

### Installation
```bash
pip install -r requirements.txt
```

### Usage
Run any script using Python:
```bash
python transcribe.py
```
The scripts will automatically load settings from `transcribe_config.json`.

---

## 📁 Project Structure
- `input/`: Place your source audio files here.
- `output/`: Generated Markdown summaries and enhanced text.
- `transcribe_config.json`: Central configuration file.
- `app.py`: Flask Web Dashboard & API Server.
- `job_manager.py`: Manages the single-worker task queue.
- `api_processing.py`: Handles single-file API transcription requests.
- `transcribe.py`: Full transcription + summarization pipeline (batch).
- `transcribe_only.py`: Only performs transcription (batch).
- `summarize_text.py`: Generates summaries and refines transcripts into enhanced text (batch).
- `templates/` & `static/`: Web UI components.
