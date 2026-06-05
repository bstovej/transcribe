# Project Instructions: Transcribe and Summarize

This project provides a comprehensive toolkit for batch transcribing audio files using OpenAI's Whisper model and summarizing those transcriptions using a local LLM via a llama.cpp server (OpenAI-compatible API). It includes a Flask-based web dashboard and a robust API for external integration.

## Project Overview

- **Purpose:** Automate the transcription of audio/video files and generate insightful summaries.
- **Main Technologies:**
    - **Python (Flask):** Backend API and UI server.
    - **JavaScript (Vanilla):** Frontend dashboard logic.
    - **OpenAI Whisper:** Local transcription model.
    - **llama.cpp server:** Local LLM API for text summarization.
    - **Docker & Docker Compose:** Containerization.

## Architecture & Workflow

The project is structured around several specialized components:

- `app.py`: Flask entry point.
- `job_manager.py`: Centralized job queue and single-worker thread for resource management.
- `api_processing.py`: Logic for processing single-file API requests.
- `transcribe.py`: Full batch pipeline (Transcribe -> Summarize -> Archive).
- `transcribe_only.py`, `summarize_text.py`: Batch utility scripts.

### Concurrency Model
To prevent resource exhaustion (Whisper is OOM-prone), all transcription tasks (UI and API) are routed through a **single-worker queue**. Jobs are processed sequentially in the order they are received.

## Setup and Execution

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
- **Run Pipeline:**
  ```bash
  python transcribe.py
  ```

## Configuration

Settings are managed in `transcribe_config.json`. Key parameters include:

- `llm_url`: The OpenAI-compatible API endpoint (e.g., `http://localhost:8080/v1/chat/completions`).
- `model_name`: The model name to pass in the request.
- `whisper_model`: The size of the Whisper model (`tiny`, `base`, `small`, `medium`, `large`).
- `input_dir` & `output_dir`: Paths for source audio and generated summaries.

## Directory Structure

- `input/`: Source audio/video files for processing.
    - `transcribed-audio/`: Archive of processed source files.
    - `transcripts/`: (Optional/User managed) location for intermediate transcripts.
- `output/`: Final Markdown summaries and enhanced text.
- `journal/`: Project-related notes and logs.

## Development Conventions

- **Stateless Scripts:** Scripts are designed to be run independently or via the dashboard.
- **Error Handling:** Transcription and API calls are wrapped in try-except blocks with logging to stdout.
- **Dynamic Configuration:** Scripts reload configuration via `config_loader.py` which respects the `TRANSCRIBE_CONFIG_PATH` environment variable.
