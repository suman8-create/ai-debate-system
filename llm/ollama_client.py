import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self):
        self.base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = getattr(settings, "OLLAMA_MODEL", "llama3:8b")
        self.embed_model = getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text")

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7) -> str:
        """Chat completion with keep_alive to keep model warm in VRAM across turns."""
        url = f"{self.base_url}/api/chat"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": temperature,
                "num_ctx": 4096
            }
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    return res.json().get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
        return ""

    def generate_json(self, prompt: str) -> Any:
        """Requests strict JSON format output from Ollama."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "keep_alive": "30m",
            "options": {
                "temperature": 0.2
            }
        }
        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    content = res.json().get("message", {}).get("content", "{}")
                    return json.loads(content)
        except Exception as e:
            logger.warning(f"Ollama JSON parse error: {e}")
        return {}

    def get_embedding(self, text: str) -> List[float]:
        """Fetches text embedding vector from Ollama."""
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.embed_model,
            "input": text,
            "keep_alive": "30m"
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    embeddings = res.json().get("embeddings", [])
                    if embeddings:
                        return embeddings[0]
        except Exception as e:
            logger.warning(f"Ollama embedding error: {e}")
        return []

ollama_client = OllamaClient()