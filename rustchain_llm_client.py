#!/usr/bin/env python3
"""
RustChain Arena - Unified LLM Transport Client

Single class `LLMClient` with one method `chat(messages, max_tokens, temperature)`.
Three backends selected by env var `LLM_BACKEND`:
  - openai (default): POSTs to OPENAI_BASE_URL (default POWER8 GPT-OSS 120B at
    http://100.75.100.89:8082) using OpenAI chat-completions schema. Model from
    OPENAI_MODEL (default gpt-oss-120b-Q4_K_M-00001-of-00002.gguf).
  - ollama: POSTs to OLLAMA_BASE_URL (default http://localhost:11434) using
    Ollama /api/chat schema. Model from OLLAMA_MODEL (default llama3).
  - mock: returns a canned string for offline development.

Hard 8-second timeout per request so a hung backend cannot freeze the game.
On any exception or timeout returns None; the caller decides whether to use
its own static fallback (both bot_brain.py and announcer.py already have
fallback ladders in place).
"""

import os
import requests
from typing import List, Dict, Optional

DEFAULT_TIMEOUT = 8.0

OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://100.75.100.89:8082")
OPENAI_MODEL = os.environ.get(
    "OPENAI_MODEL", "gpt-oss-120b-Q4_K_M-00001-of-00002.gguf"
)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

MOCK_RESPONSE = "[mock] Tactical decision: hold position, target nearest hostile."


class LLMClient:
    """Transport-agnostic chat client. Pick backend via LLM_BACKEND env var."""

    def __init__(self, backend: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT):
        self.backend = (backend or os.environ.get("LLM_BACKEND", "openai")).lower()
        self.timeout = timeout

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 200,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """Send chat-style messages, return assistant text or None on failure."""
        try:
            if self.backend == "openai":
                return self._chat_openai(messages, max_tokens, temperature)
            elif self.backend == "ollama":
                return self._chat_ollama(messages, max_tokens, temperature)
            elif self.backend == "mock":
                return MOCK_RESPONSE
            else:
                print(f"[LLMClient] Unknown backend: {self.backend!r}")
                return None
        except requests.exceptions.Timeout:
            print(f"[LLMClient] {self.backend} timed out after {self.timeout}s")
            return None
        except Exception as e:
            print(f"[LLMClient] {self.backend} error: {e}")
            return None

    def _chat_openai(self, messages, max_tokens, temperature) -> Optional[str]:
        url = f"{OPENAI_BASE_URL.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": OPENAI_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        r = requests.post(url, json=payload, timeout=self.timeout)
        if r.status_code != 200:
            print(f"[LLMClient] openai HTTP {r.status_code}: {r.text[:200]}")
            return None
        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return None
        msg = choices[0].get("message") or {}
        text = msg.get("content")
        return text.strip() if text else None

    def _chat_ollama(self, messages, max_tokens, temperature) -> Optional[str]:
        url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        r = requests.post(url, json=payload, timeout=self.timeout)
        if r.status_code != 200:
            print(f"[LLMClient] ollama HTTP {r.status_code}: {r.text[:200]}")
            return None
        data = r.json()
        msg = data.get("message") or {}
        text = msg.get("content")
        return text.strip() if text else None


if __name__ == "__main__":
    test_messages = [
        {"role": "system", "content": "You are a terse arena bot."},
        {"role": "user", "content": "Say a one-line taunt."},
    ]
    for backend in ("mock", "openai", "ollama"):
        print(f"\n--- backend={backend} ---")
        client = LLMClient(backend=backend, timeout=8.0)
        reply = client.chat(test_messages, max_tokens=40, temperature=0.7)
        if reply is None:
            print(f"  (no reply / fallback path)")
        else:
            print(f"  {reply}")
