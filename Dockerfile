# Use a Python 3.10 slim image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Environment variables with default values
ENV LLM_URL=http://host.docker.internal:8080/v1/chat/completions
ENV MODEL_NAME=gemma-4-12b

# Define the default command to run transcribe.py
# Users can override this to run other scripts
CMD ["python", "transcribe.py"]
