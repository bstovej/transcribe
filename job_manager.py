import threading
import queue
import uuid
import time
import io
import sys
from contextlib import redirect_stdout

# Job Types
TYPE_PIPELINE = "pipeline"
TYPE_TRANSCRIBE = "transcribe"
TYPE_SUMMARIZE = "summarize"
TYPE_ENHANCE = "enhance"
TYPE_SINGLE_API = "single_api"

# Status Types
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

class JobManager:
    def __init__(self):
        self.jobs = {}  # job_id -> data
        self.queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def add_job(self, job_type, params):
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "type": job_type,
            "params": params,
            "status": STATUS_PENDING,
            "logs": [],
            "result": None,
            "created_at": time.time()
        }
        self.queue.put(job_id)
        return job_id

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def _worker(self):
        # Delayed imports to avoid circular dependencies if any
        import transcribe
        import transcribe_only
        import summarize_text
        import enhance_text
        import api_processing

        while True:
            job_id = self.queue.get()
            job = self.jobs[job_id]
            job["status"] = STATUS_PROCESSING
            
            # Custom stream to capture logs in real-time
            class LogStream(io.StringIO):
                def __init__(self, logs_list):
                    super().__init__()
                    self.logs_list = logs_list
                def write(self, s):
                    if s.strip():
                        self.logs_list.append(s.strip())
                    return super().write(s)

            log_stream = LogStream(job["logs"])

            try:
                with redirect_stdout(log_stream):
                    params = job["params"]
                    if job["type"] == TYPE_PIPELINE:
                        transcribe.run_pipeline(
                            params.get("input_dir"), 
                            params.get("output_dir"), 
                            params.get("whisper_model")
                        )
                    elif job["type"] == TYPE_TRANSCRIBE:
                        transcribe_only.transcribe_files(
                            params.get("input_dir"), 
                            params.get("whisper_model")
                        )
                    elif job["type"] == TYPE_SUMMARIZE:
                        summarize_text.process_transcriptions(
                            params.get("input_dir"), 
                            params.get("output_dir")
                        )
                    elif job["type"] == TYPE_ENHANCE:
                        summarize_text.process_transcriptions(
                            params.get("input_dir"), 
                            params.get("output_dir"),
                            action="enhance"
                        )
                    elif job["type"] == TYPE_SINGLE_API:
                        result = api_processing.process_single_file(
                            params.get("file_path"),
                            params.get("output_dir"),
                            params.get("whisper_model"),
                            params.get("summarize", True)
                        )
                        job["result"] = result
                
                job["status"] = STATUS_COMPLETED
            except Exception as e:
                job["status"] = STATUS_FAILED
                job["logs"].append(f"ERROR: {str(e)}")
            finally:
                self.queue.task_done()

# Singleton instance
job_manager = JobManager()
