# Product Requirements Document (PRD): Transcribe and Summarize

## 1. Executive Summary
This project provides a robust, locally-hosted solution for transcribing audio/video files and generating intelligent summaries using local speech models (Whisper) and local LLMs (hosted via **llama.cpp server** or **Ollama**). It is designed for privacy-conscious users who want to avoid cloud-based transcription and LLM services.

## 2. Target Audience
- Researchers and students transcribing interviews/lectures.
- Professionals summarizing meetings.
- Developers looking for a self-hosted transcription API.

## 3. Core Functional Requirements

### 3.1 Transcription
- **Engines:**
    - **Local Whisper Pipeline:** Uses Hugging Face Transformers Whisper (`openai/whisper-small` cached locally for offline execution) with direct FFmpeg audio decoding to reliably handle all media containers (including unoptimized M4A/MP4 streams).
    - **Multimodal LLM Transcription:** Supports transcription via multimodal OpenAI-compatible API endpoints using base64-encoded `input_audio` payloads (`transcribe_only.py`).
- **Supported Formats:** `.mp3`, `.m4a`, `.wav`, `.mp4`, `.mpeg`, `.mpga`, `.webm`.
- **Modes:** 
    - **Batch Processing:** Monitor and process files in bulk from an input directory.
    - **Single-File Processing:** Support targeting an individual media file via CLI or REST API.
    - **Single-File API:** Accept file uploads via REST API and process them individually.
- **Model Support:** Whisper local models and multimodal LLM models (e.g. `gemma-4-12b`, `qwen3.5:9b`).

### 3.2 Summarization & Text Enhancement
- **Backend:** Local LLM engines providing OpenAI-compatible endpoints, specifically **llama.cpp server** and **Ollama**.
- **Features:**
    - Structured Markdown summaries highlighting key takeaways, challenges, and core insights (formatted without emojis).
    - Text translation to English for non-English transcriptions prior to summarization.
    - **YAML Frontmatter Templating:** Prepend customizable frontmatter to markdown summaries and enhancements based on template files (e.g. `templates/tp_header.md`). Supports dynamic token interpolation:
        - `{{date}}` / `{{date:FORMAT}}`
        - `{{time}}` / `{{time:FORMAT}}`
        - `{{title}}`
        - `{{source}}`
    - Frontmatter deduplication: Automatically strips existing frontmatter blocks to prevent duplicated headers.
- **Flexibility:**
    - `summarize_text.py` supports `--action summarize` and `--action enhance` (grammar correction and readability improvement).

### 3.3 Configuration & CLI Control
- **Configuration File:** Initialized via `cp sample_transcribe_config.json transcribe_config.json`, defining:
    - `llm_url`: Target LLM API endpoint.
    - `model_name`: Model identifier for API requests.
    - `input_dir`: Source directory for recordings.
    - `output_dir`: Destination directory for summaries and enhanced documents.
    - `template_path`: Path to frontmatter template file.
- **CLI Overrides:** Command-line flags available across `transcribe.py`, `summarize_text.py`, and `transcribe_only.py` (`--input`, `--output`, `--llm-url`, `--model-name`, `--template`, `--action`).

### 3.4 Web Dashboard
- **Backend:** Flask.
- **Frontend:** Vanilla JavaScript/HTML/CSS.
- **Features:**
    - Live execution logs via Server-Sent Events (SSE).
    - Configuration management (LLM URL, Whisper Model, Paths).
    - Output file browser.
    - Status monitoring for background jobs.

### 3.5 Concurrency & Stability
- **Job Management:** Use a single-worker queue to process resource-intensive transcription tasks sequentially to prevent memory exhaustion (OOM).
- **Async API:** External clients receive a `job_id` and poll for results.

## 4. Technical Requirements
- **Language:** Python 3.10+
- **Containerization:** Docker & Docker Compose.
- **Dependencies:** PyTorch, Transformers, FFmpeg, Requests, Flask.
- **Infrastructure:** Local LLM runtime—either **llama.cpp server** or **Ollama** (or any OpenAI-compatible server).
- **Storage:** Local filesystem for input, output, frontmatter templates, and archiving.

## 5. Security & Privacy
- **Local First:** All data processing stays on the user's machine/network.
- **Web UI:** Bound to `127.0.0.1` by default in Docker for local access only.
- **CORS:** Configurable to allow trusted network clients.

## 6. Success Metrics
- Successful transcription of all supported media formats without demuxing failures.
- Stable execution without OOM crashes during long batch runs.
- Consistent YAML frontmatter metadata generated for Markdown knowledge bases (e.g. Obsidian).
- Real-time log visibility in the web dashboard.
- Reliable API access for external transcription requests.
