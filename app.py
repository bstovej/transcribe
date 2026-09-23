from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import os
import json
import time
from pathlib import Path
from config_loader import config
from job_manager import job_manager, TYPE_PIPELINE, TYPE_TRANSCRIBE, TYPE_SUMMARIZE, TYPE_ENHANCE, TYPE_SINGLE_API

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = config.get("input_dir", "./input")
OUTPUT_FOLDER = config.get("output_dir", "./output")

# Ensure directories exist
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    config_path = os.getenv("TRANSCRIBE_CONFIG_PATH", "transcribe_config.json")
    
    if request.method == 'POST':
        new_config = request.json
        with open(config_path, 'w') as f:
            json.dump(new_config, f, indent=2)
        # Update current in-memory config
        config.update(new_config)
        return jsonify({"status": "success", "config": config})
    
    return jsonify(config)

@app.route('/api/files', methods=['GET'])
def list_files():
    output_path = Path(config.get("output_dir", "./output"))
    if not output_path.exists():
        return jsonify([])
    
    files = [f.name for f in sorted(output_path.glob("*.md"))]
    return jsonify(files)

@app.route('/api/run_task', methods=['POST'])
def run_task():
    data = request.json
    task_name = data.get("task")
    
    task_map = {
        "pipeline": TYPE_PIPELINE,
        "transcribe": TYPE_TRANSCRIBE,
        "summarize": TYPE_SUMMARIZE,
        "enhance": TYPE_ENHANCE
    }
    
    if task_name not in task_map:
        return jsonify({"error": "Invalid task"}), 400
    
    job_id = job_manager.add_job(task_map[task_name], {
        "input_dir": config.get("input_dir"),
        "output_dir": config.get("output_dir"),
        "whisper_model": config.get("whisper_model")
    })
    
    return jsonify({"job_id": job_id})

@app.route('/api/stream_log/<job_id>')
def stream_log(job_id):
    def generate():
        job = job_manager.get_job(job_id)
        if not job:
            yield "data: {\"error\": \"Job not found\"}\n\n"
            return

        last_idx = 0
        while job["status"] in ["pending", "processing"]:
            if last_idx < len(job["logs"]):
                for i in range(last_idx, len(job["logs"])):
                    yield f"data: {json.dumps({'log': job['logs'][i], 'status': job['status']})}\n\n"
                last_idx = len(job["logs"])
            time.sleep(0.5)
        
        # Final status and logs
        if last_idx < len(job["logs"]):
            for i in range(last_idx, len(job["logs"])):
                yield f"data: {json.dumps({'log': job['logs'][i], 'status': job['status']})}\n\n"
        
        yield f"data: {json.dumps({'status': job['status'], 'done': True})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filename = file.filename
    file_path = os.path.join(config.get("input_dir", "./input"), filename)
    file.save(file_path)
    
    job_id = job_manager.add_job(TYPE_SINGLE_API, {
        "file_path": file_path,
        "output_dir": config.get("output_dir"),
        "summarize": True
    })
    
    return jsonify({"job_id": job_id, "status": "queued"})

@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    job = job_manager.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify({
        "status": job["status"],
        "logs": job["logs"],
        "result": job["result"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501, debug=True)
