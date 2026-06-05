# Migration Plan: Streamlit to Flask + JS & API Extension

## Background & Motivation
The project currently uses Streamlit for its web dashboard. The goal is to migrate to a standard web architecture using the Flask framework for the backend and vanilla JavaScript/HTML/CSS for the frontend. Additionally, we are extending the backend to act as a robust API server, allowing external applications on the network to upload files and receive transcriptions asynchronously.

Because Whisper is highly resource-intensive, we cannot allow concurrent transcription tasks. To ensure system stability, the backend will implement a dedicated single-worker queue to process tasks sequentially.

## Scope & Impact
- **Backend:** `app.py` will be completely rewritten as a Flask application.
- **Frontend:** New directories (`templates/`, `static/`) will be introduced to house the HTML, CSS, and JS files.
- **Dependencies:** `streamlit` will be removed; `flask` and `flask-cors` will be added.
- **Execution:** Docker and local start commands will change to reflect Flask usage (bound to 0.0.0.0).
- **Core Scripts:** Existing batch scripts (`transcribe.py`, etc.) will remain untouched. A new script (`api_processing.py`) will be introduced to handle single-file API requests.
- **Concurrency Model:** A single background worker thread and a job queue will be introduced to prevent resource exhaustion.
- **API Functionality:** New endpoints will be added for file upload, async job queuing, and status polling.

## Proposed Solution & Implementation Steps

### Phase 1: Dependency & Structure Updates
1.  Update `requirements.txt`: Remove `streamlit`, add `flask` and `flask-cors`.
2.  Create directory structure: `templates/` and `static/`.

### Phase 2: Core Architecture: Queues & Workers
1.  **Create `job_manager.py`:**
    - Implement a `queue.Queue` to hold pending jobs.
    - Implement an in-memory dictionary: `JOBS = { "job_id": {"type": "batch|single", "status": "pending|processing|completed|failed", "log": [], "result": None} }`.
    - Create a single dedicated `worker_thread` that continuously pulls jobs from the queue, executes them (either calling `transcribe.py` functions or `api_processing.py` functions), captures the output, and updates the `JOBS` dictionary upon completion.

### Phase 3: Core UI Backend Development (Flask)
1.  **Rewrite `app.py`:**
    - Initialize a Flask app with CORS enabled. Start the `worker_thread` on startup.
    - Route `/`: Serve `index.html`.
    - Route `/api/config` (GET/POST): Retrieve and update settings.
    - Route `/api/files` (GET): List `.md` files in the output directory.
    - Route `/api/run_task` (POST): Accepts a batch task request (e.g., `pipeline`), generates a `job_id`, adds it to the queue, and returns the ID.
    - Route `/api/stream_log/<job_id>` (GET): An SSE endpoint that streams the `log` array of a specific job as it updates.

### Phase 4: API & Single-File Extension
1.  **Create `api_processing.py`:**
    - Implement a function to transcribe and (optionally) summarize a *single* file, returning the result string.
2.  **Add External API Endpoints to `app.py`:**
    - `POST /api/upload`: Accepts a multipart file, saves it to `input/`, generates a `job_id`, adds an `api_processing` job to the queue, and returns `{"job_id": "<id>"}`.
    - `GET /api/status/<job_id>` (now includes log streaming): Returns the current status, logs, and, if completed, the resulting transcription text.

### Phase 5: Frontend Development (HTML/JS)
1.  **`templates/index.html`:** Create a dashboard layout mirroring the current UI.
2.  **`static/style.css`:** Apply a clean, modern style.
3.  **`static/app.js`:**
    - Fetch config, populate sidebar, and fetch output files.
    - Handle task execution by POSTing to `/api/run_task`, receiving a `job_id`, and then opening an `EventSource` to `/api/stream_log/<job_id>` to render live logs.

### Phase 6: Documentation & Docker Updates
1.  Update `docker-compose.yml` to run the Flask app (`flask run --host=0.0.0.0 --port=8501`).
2.  Update `README.md` and `GEMINI.md` to document the new architecture, queue behavior, and API endpoints.

## Verification
- **Concurrency Test:** Initiate a batch "Full Pipeline" task via the UI, then immediately upload a file via `/api/upload`. Verify that the upload succeeds instantly (returning a pending job ID) and that processing of the uploaded file only begins *after* the batch job completes.
- **UI Test:** Verify config updates, log streaming, and file browsing function correctly.
- **API Test:** Verify external clients can successfully upload files and poll for results.
