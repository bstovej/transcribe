<<<<<<< HEAD
# transcribe
Transcribe and summmarize audio and video files. 
=======
# Transcribe and Summarize

This project provides a set of Python scripts for batch transcribing audio files using OpenAI's Whisper model and summarizing the transcriptions using a local LLM via Ollama. 

Now includes a **Docker-based environment** and a **Web Dashboard** for easier management.

---

## 🚀 Getting Started with Docker (Recommended)

The easiest way to run the project is using Docker and Docker Compose. This ensures all dependencies like `ffmpeg` and Python libraries are correctly configured.

### Prerequisites
1.  **Docker & Docker Compose** installed.
2.  **Ollama** running on your host machine.
    *   Pull the required model: `ollama pull llama3.2:latest`
    *   Ensure Ollama is accessible from Docker (default config uses `host.docker.internal`).

### 1. Configuration
Settings are managed in `transcribe_config.json`. You can modify this file to change:
*   `ollama_url`: The API endpoint for Ollama.
*   `model_name`: The LLM model for summarization.
*   `whisper_model`: The Whisper model size (`tiny`, `base`, `small`, `medium`, `large`).
*   `input_dir` & `output_dir`: Folder paths inside the container.

### 2. Build and Run the Web UI
Launch the Streamlit dashboard to manage tasks visually:
```bash
docker-compose build
docker-compose up ui
```
**Security Note:** For your protection, the UI is bound to `127.0.0.1`. It is **only** accessible from your local machine at: **http://localhost:8501**

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
3.  **Ollama** running locally.

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
- `app.py`: Streamlit Web Dashboard.
- `transcribe.py`: Full transcription + summarization pipeline.
- `transcribe_only.py`: Only performs transcription.
- `summarize_text.py`: Generates summaries from existing transcripts.
- `enhance_text.py`: Refines existing transcripts into summaries.
>>>>>>> f85b14d (first commit)
