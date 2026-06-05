import json
import os
from pathlib import Path

DEFAULT_CONFIG_PATH = "transcribe_config.json"

def load_config():
    """
    Loads configuration from JSON file specified by TRANSCRIBE_CONFIG_PATH 
    or the default location.
    """
    config_path = os.getenv("TRANSCRIBE_CONFIG_PATH", DEFAULT_CONFIG_PATH)
    
    if not os.path.exists(config_path):
        print(f"Warning: Config file not found at {config_path}. Using default internal values.")
        return {
            "llm_url": "http://localhost:8080/v1/chat/completions",
            "model_name": "gpt-3.5-turbo",
            "whisper_model": "base",
            "input_dir": "./input",
            "output_dir": "./output"
        }

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file: {e}. Using default internal values.")
        return {
            "llm_url": "http://localhost:8080/v1/chat/completions",
            "model_name": "gpt-3.5-turbo",
            "whisper_model": "base",
            "input_dir": "./input",
            "output_dir": "./output"
        }

# Pre-load configuration
config = load_config()
