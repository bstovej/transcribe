import streamlit as st
import os
import transcribe
import transcribe_only
import summarize_text
import enhance_text
from config_loader import config
from contextlib import redirect_stdout
import io

st.set_page_config(page_title="Audio Transcription & Summarization", layout="wide")

st.title("🎙️ Audio Processing Dashboard")

# Sidebar configuration
st.sidebar.header("Configuration")
ollama_url = st.sidebar.text_input("Ollama URL", config.get("ollama_url", "http://host.docker.internal:11434/api/chat"))
model_name = st.sidebar.text_input("LLM Model Name", config.get("model_name", "llama3.2:latest"))
whisper_model = st.sidebar.selectbox("Whisper Model", ["tiny", "base", "small", "medium", "large"], 
                                     index=["tiny", "base", "small", "medium", "large"].index(config.get("whisper_model", "base")))

st.sidebar.divider()
input_dir = st.sidebar.text_input("Input Directory", config.get("input_dir", "./input"))
output_dir = st.sidebar.text_input("Output Directory", config.get("output_dir", "./output"))

# Update script configuration dynamically
transcribe.OLLAMA_URL = ollama_url
transcribe.MODEL_NAME = model_name
transcribe.WHISPER_MODEL = whisper_model
transcribe.INPUT_DIR = input_dir
transcribe.OUTPUT_DIR = output_dir

transcribe_only.WHISPER_MODEL = whisper_model
transcribe_only.INPUT_DIR = input_dir

summarize_text.OLLAMA_URL = ollama_url
summarize_text.MODEL_NAME = model_name
summarize_text.INPUT_DIR = input_dir
summarize_text.OUTPUT_DIR = output_dir

enhance_text.OLLAMA_URL = ollama_url
enhance_text.MODEL_NAME = model_name
enhance_text.INPUT_DIR = input_dir
enhance_text.OUTPUT_DIR = output_dir

# Main UI
st.subheader("Select Task")
col1, col2, col3, col4 = st.columns(4)

task = None
if col1.button("🚀 Run Full Pipeline", use_container_width=True):
    task = "pipeline"
if col2.button("✍️ Transcribe Only", use_container_width=True):
    task = "transcribe"
if col3.button("📝 Summarize Only", use_container_width=True):
    task = "summarize"
if col4.button("✨ Enhance Text", use_container_width=True):
    task = "enhance"

if task:
    st.divider()
    st.info(f"Running task: **{task.upper()}**...")
    
    output_buffer = io.StringIO()
    
    try:
        with redirect_stdout(output_buffer):
            if task == "pipeline":
                transcribe.run_pipeline(input_dir, output_dir, whisper_model)
            elif task == "transcribe":
                transcribe_only.transcribe_files(input_dir, whisper_model)
            elif task == "summarize":
                summarize_text.process_transcriptions(input_dir, output_dir)
            elif task == "enhance":
                enhance_text.process_transcriptions(input_dir, output_dir)
        
        st.success("✅ Task completed successfully!")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
    
    with st.expander("View Logs", expanded=True):
        st.text(output_buffer.getvalue())

# File browser simulation
st.divider()
st.subheader("📁 Output Files")
if os.path.exists(output_dir):
    files = os.listdir(output_dir)
    if files:
        for f in sorted(files):
            if f.endswith(".md"):
                st.markdown(f"- **{f}**")
    else:
        st.write("No output files found.")
else:
    st.write(f"Output directory '{output_dir}' does not exist yet.")
