"""
engine_llm.py - Local LLM Engine (Llama / Ollama backend).
Connects to local Ollama server, handles model discovery, dynamic selection,
auto-starting Ollama daemon if inactive, and streaming token output.
"""

import requests
import json
import time
import subprocess
import shutil
import os
from typing import Generator, List, Dict, Any, Optional

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"

class LocalLLMEngine:
    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL, preferred_model: str = "llama3.2:1b"):
        self.base_url = base_url.rstrip("/")
        self.active_model = preferred_model
        self.available_models: List[str] = []
        self._ensure_ollama_running()
        self.refresh_available_models()

    def _find_ollama_binary(self) -> Optional[str]:
        """Locates ollama.exe on the system."""
        found = shutil.which("ollama")
        if found:
            return found
        default_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
            r"C:\Users\RYZEN\AppData\Local\Programs\Ollama\ollama.exe",
            r"C:\Program Files\Ollama\ollama.exe"
        ]
        for p in default_paths:
            if os.path.isfile(p):
                return p
        return None

    def _ensure_ollama_running(self) -> bool:
        """Checks if Ollama is listening; if not, automatically launches it in the background."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass

        # Not running - attempt to start daemon
        bin_path = self._find_ollama_binary()
        if not bin_path:
            return False

        try:
            # On Windows, start detached without pop-up console window
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW | getattr(subprocess, "DETACHED_PROCESS", 0x00000008)

            subprocess.Popen(
                [bin_path, "serve"],
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True
            )

            # Wait up to 3.5 seconds for port to open
            for _ in range(12):
                time.sleep(0.3)
                try:
                    r = requests.get(f"{self.base_url}/api/tags", timeout=0.8)
                    if r.status_code == 200:
                        return True
                except Exception:
                    pass
        except Exception:
            return False

        return False

    def refresh_available_models(self) -> List[str]:
        """Queries Ollama for list of installed models."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                models_data = resp.json().get("models", [])
                self.available_models = [m.get("name", "") for m in models_data if m.get("name")]
                
                # If active_model is not installed, select best match
                if self.active_model not in self.available_models:
                    # Look for any llama model first
                    llama_models = [m for m in self.available_models if "llama" in m.lower()]
                    if llama_models:
                        self.active_model = llama_models[0]
                    elif "qwen2.5-coder:3b" in self.available_models:
                        self.active_model = "qwen2.5-coder:3b"
                    elif "qwen2.5-coder:1.5b-instruct" in self.available_models:
                        self.active_model = "qwen2.5-coder:1.5b-instruct"
                    elif self.available_models:
                        self.active_model = self.available_models[0]
            return self.available_models
        except Exception:
            return []

    def set_model(self, model_name: str) -> bool:
        """Sets the active model if available."""
        self.refresh_available_models()
        # Direct match or partial match
        for m in self.available_models:
            if m.lower() == model_name.lower() or model_name.lower() in m.lower():
                self.active_model = m
                return True
        return False

    def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Generator[str, None, None]:
        """
        Streams response tokens from the local LLM with automatic recovery.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.active_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": 2048
            }
        }

        # Try sending request, auto-start if server is down
        for attempt in range(2):
            try:
                with requests.post(url, json=payload, stream=True, timeout=60) as resp:
                    if resp.status_code != 200:
                        yield f"[Error from local LLM (HTTP {resp.status_code})]"
                        return

                    for line in resp.iter_lines():
                        if line:
                            chunk = json.loads(line.decode("utf-8"))
                            msg = chunk.get("message", {})
                            content = msg.get("content", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                break
                return
            except requests.exceptions.ConnectionError:
                if attempt == 0:
                    yield "[Waking up local Ollama server...]\n"
                    if self._ensure_ollama_running():
                        continue
                yield f"\n[Error: Unable to connect to local Ollama server at {self.base_url}. Make sure Ollama is installed and running.]"
                return
            except Exception as e:
                yield f"\n[LLM Error: {str(e)}]"
                return
