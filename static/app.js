document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    loadFiles();

    document.getElementById('save-config').addEventListener('click', saveConfig);
});

async function loadConfig() {
    const response = await fetch('/api/config');
    const config = await response.json();
    
    document.getElementById('llm_url').value = config.llm_url;
    document.getElementById('model_name').value = config.model_name;
    document.getElementById('whisper_model').value = config.whisper_model;
    document.getElementById('input_dir').value = config.input_dir;
    document.getElementById('output_dir').value = config.output_dir;
}

async function saveConfig() {
    const config = {
        llm_url: document.getElementById('llm_url').value,
        model_name: document.getElementById('model_name').value,
        whisper_model: document.getElementById('whisper_model').value,
        input_dir: document.getElementById('input_dir').value,
        output_dir: document.getElementById('output_dir').value
    };

    const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });

    if (response.ok) {
        alert('Configuration saved successfully!');
    } else {
        alert('Failed to save configuration.');
    }
}

async function loadFiles() {
    const response = await fetch('/api/files');
    const files = await response.json();
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '';
    
    if (files.length === 0) {
        fileList.innerHTML = '<li>No output files found.</li>';
        return;
    }

    files.forEach(file => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${file}</strong>`;
        fileList.appendChild(li);
    });
}

async function runTask(task) {
    const statusArea = document.getElementById('status-area');
    const logContainer = document.getElementById('log-container');
    const statusLabel = document.getElementById('current-task-label');
    const statusBadge = document.getElementById('job-status-badge');

    statusArea.style.display = 'block';
    logContainer.innerHTML = '';
    statusLabel.innerText = `Running task: ${task.toUpperCase()}...`;
    updateStatusBadge(statusBadge, 'pending');

    const response = await fetch('/api/run_task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task })
    });

    const data = await response.json();
    if (data.job_id) {
        const eventSource = new EventSource(`/api/stream_log/${data.job_id}`);
        
        eventSource.onmessage = (event) => {
            const payload = JSON.parse(event.data);
            
            if (payload.log) {
                const line = document.createElement('div');
                line.textContent = payload.log;
                logContainer.appendChild(line);
                logContainer.scrollTop = logContainer.scrollHeight;
            }
            
            if (payload.status) {
                updateStatusBadge(statusBadge, payload.status);
            }
            
            if (payload.done) {
                eventSource.close();
                loadFiles();
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            updateStatusBadge(statusBadge, 'failed');
        };
    }
}

function updateStatusBadge(badge, status) {
    badge.className = `status-badge status-${status}`;
    badge.innerText = status.toUpperCase();
}
