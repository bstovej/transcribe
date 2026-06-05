# Product Requirements Document (PRD): Transcribe and Summarize

## 1. Executive Summary
This project provides a robust, locally-hosted solution for transcribing audio/video files and generating intelligent summaries. It is designed for privacy-conscious users who want to avoid cloud-based transcription and LLM services.

## 2. Target Audience
- Researchers and students transcribing interviews/lectures.
- Professionals summarizing meetings.
- Developers looking for a self-hosted transcription API.

## 3. Core Functional Requirements

### 3.1 Transcription
- **Engine:** OpenAI Whisper (Local).
- **Supported Formats:** `.mp3`, `.m4a`, `.wav`, `.mp4`, `.mpeg`, `.mpga`, `.webm`.
- **Modes:** 
    - **Batch Processing:** Monitor a local folder and process files in bulk.
    - **Single-File API:** Accept file uploads via REST API and process them individually.
- **Model Support:** Allow selection of Whisper model sizes (`tiny` to `large`).

### 3.2 Summarization
- **Backend:** llama.cpp server (OpenAI-compatible API).
- **Features:** Generate Markdown summaries including key highlights, challenges, and takeaways.
- **Flexibility:** Support "Summarize Only" and "Enhance Text" tasks for existing transcripts.

### 3.3 Web Dashboard
- **Backend:** Flask.
- **Frontend:** Vanilla JavaScript/HTML/CSS.
- **Features:**
    - Live execution logs via Server-Sent Events (SSE).
    - Configuration management (LLM URL, Whisper Model, Paths).
    - Output file browser.
    - Status monitoring for background jobs.

### 3.4 Concurrency & Stability
- **Job Management:** Use a single-worker queue to process resource-intensive transcription tasks sequentially to prevent memory exhaustion (OOM).
- **Async API:** External clients receive a `job_id` and poll for results.

## 4. Technical Requirements
- **Language:** Python 3.10+
- **Containerization:** Docker & Docker Compose.
- **Infrastructure:** Local llama.cpp server instance.
- **Storage:** Local file system for input, output, and archiving.

## 5. Security & Privacy
- **Local First:** All data processing stays on the user's machine/network.
- **Web UI:** Bound to `127.0.0.1` by default in Docker for local access only.
- **CORS:** Configurable to allow trusted network clients.

## 6. Success Metrics
- Successful transcription of all supported media formats.
- Stable execution without OOM crashes during long batch runs.
- Real-time log visibility in the web dashboard.
- Reliable API access for external transcription requests.
