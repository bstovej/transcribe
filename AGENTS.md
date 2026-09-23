# Project Instructions: Transcribe and Summarize

This project provides a comprehensive toolkit for batch transcribing audio files and summarizing those transcriptions using local LLMs hosted via **llama.cpp server** or **Ollama** (OpenAI-compatible API). It includes a Flask-based web dashboard and a robust API for external integration.

## Project Overview

- **Purpose:** Automate the transcription of audio/video files and generate insightful summaries.
- **Main Technologies:**
    - **Python (Flask):** Backend API and UI server.
    - **JavaScript (Vanilla):** Frontend dashboard logic.
    - **Local LLM Engine (llama.cpp server or Ollama):** OpenAI-compatible API for text translation, summarization, enhancement, and multimodal audio transcription.
    - **Docker & Docker Compose:** Containerization.

## Architecture & Workflow

The project is structured around several specialized components:

- `app.py`: Flask entry point.
- `job_manager.py`: Centralized job queue and single-worker thread for resource management.
- `api_processing.py`: Logic for processing single-file API requests.
- `transcribe.py`: Full pipeline: Local Whisper transcription (FFmpeg decoded) -> LLM Translation -> LLM Summarization with YAML frontmatter -> Archive original audio/video.
- `transcribe_only.py`: Direct audio transcription using a multimodal LLM API (`input_audio` payload) -> Archive original media.
- `summarize_text.py`: Batch or single-file summarization (`--action summarize`) and grammar/readability enhancement (`--action enhance`) of existing transcriptions with YAML frontmatter.
- `config_loader.py`: Configuration loader with environment variable support (`TRANSCRIBE_CONFIG_PATH`).

### Concurrency Model
To prevent resource exhaustion, all transcription and summarization tasks are routed through a **single-worker queue**. Jobs are processed sequentially in the order they are received.

## Setup and Execution

### Clone the Repository
```bash
git clone https://github.com/bstovej/transcribe.git
cd transcribe
```

### Configuration
Initialize the configuration file from the provided sample:
```bash
cp sample_transcribe_config.json transcribe_config.json
```
Edit `transcribe_config.json` with local settings:
- `llm_url`: The OpenAI-compatible API endpoint (e.g., `http://localhost:8080/v1/chat/completions` for llama.cpp server or `http://localhost:11434/v1/chat/completions` for Ollama).
- `model_name`: The model identifier to pass in requests (e.g., `gemma-4-12b`, `qwen3.5:9b`).
- `input_dir`: Path for source recordings.
- `output_dir`: Path for generated Markdown summaries and enhancements.
- `template_path`: Path to the YAML frontmatter template (defaults to `./templates/tp_header.md`).

#### Frontmatter Templating
Markdown summaries and enhancements render dynamic metadata from the template specified by `template_path`. Tokens supported:
- `{{date}}` / `{{date:FORMAT}}`: Date stamp (e.g. `{{date:YYYY-MM-DD}}`).
- `{{time}}` / `{{time:FORMAT}}`: Time stamp (e.g. `{{time:YYYY-MM-DDTHH:mm}}`).
- `{{title}}`: Stem name of the processed file.
- `{{source}}`: Original filename.

Existing frontmatter blocks are stripped automatically to prevent duplicates.

### Using Docker (Recommended)
- **Build and start the Web UI:**
  ```bash
  docker-compose build
  docker-compose up ui
  ```
  Access the dashboard at `http://localhost:8501`.

### API Integration
- **Upload File:** `POST /api/upload` (accepts `file` in multipart form). Returns a `job_id`.
- **Status/Results:** `GET /api/status/<job_id>` to poll for status and final results.

### Local Setup (Non-Docker)
- **Requirements:** Python 3.10+, FFmpeg installed on host.
- **Installation:**
  ```bash
  pip install -r requirements.txt
  ```
- **Run Dashboard:**
  ```bash
  python app.py
  ```
- **CLI Script Execution:**
  - **Full Pipeline (`transcribe.py`):**
    ```bash
    python transcribe.py [--input/-i PATH] [--output/-o PATH] [--llm-url/-u URL] [--model-name/-m MODEL] [--template/-t PATH]
    ```
    *Note: Supports processing single audio/video files or an entire folder.*
  - **Summarize & Enhance (`summarize_text.py`):**
    ```bash
    python summarize_text.py [--action summarize|enhance] [--input/-i PATH] [--output/-o PATH] [--llm-url/-u URL] [--model-name/-m MODEL] [--template/-t PATH]
    ```
  - **Transcribe Only (`transcribe_only.py`):**
    ```bash
    python transcribe_only.py [--input/-i PATH] [--llm-url/-u URL] [--model-name/-m MODEL]
    ```

## Directory Structure

- `sample_transcribe_config.json`: Sample template for configuration.
- `transcribe_config.json`: User-specific active configuration file (ignored by Git).
- `input/`: Source audio/video files for processing.
    - `transcribed-audio/`: Archive of processed source files.
- `output/`: Final Markdown summaries (`*-summarized.md`) and enhanced texts (`*-enhanced.md`).
- `templates/`:
    - `tp_header.md`: Default YAML frontmatter template.
    - `index.html`: Dashboard template.
- `static/`: Frontend styles and JavaScript.
- `journal/`: Project-related notes and logs.

## Development Conventions

- **Stateless Scripts:** Scripts are designed to be run independently or via the dashboard.
- **Error Handling:** Transcription and API calls are wrapped in try-except blocks with logging to stdout.
- **Dynamic Configuration:** Scripts reload configuration via `config_loader.py` which respects the `TRANSCRIBE_CONFIG_PATH` environment variable.

