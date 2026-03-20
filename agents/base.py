"""
agents/base.py — Base Agent Class.

Provides shared LLM client logic, dual-backend support (Gemini/Ollama),
and multi-student history tracking.
"""

import os
import time
import json
from typing import Optional

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# Hardware/Environment Config
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


def detect_backend() -> tuple[str, str]:
    """Auto-detect the best available LLM backend."""
    target = os.environ.get("LLM_BACKEND", "auto").lower()
    
    # Force Gemini
    if target == "gemini" and GEMINI_AVAILABLE and GEMINI_API_KEY:
        return "gemini", "gemini-2.0-flash"
        
    # Force Ollama
    if target == "ollama" and OLLAMA_AVAILABLE:
        return "ollama", detect_model()
        
    # Auto-detect
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        return "gemini", "gemini-2.0-flash"
        
    if OLLAMA_AVAILABLE:
        try:
            client = ollama.Client(host=OLLAMA_HOST)
            client.list()
            return "ollama", detect_model()
        except Exception:
            pass
            
    return "offline", None


def detect_model() -> str:
    """Detect the best model available in Ollama."""
    if not OLLAMA_AVAILABLE:
        return None
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        models = [m['name'] for m in client.list()['models']]
        # Order of preference
        for pref in ["qwen2.5:7b", "phi3.5:latest", "gemma2:2b", "gemma:2b", "llama3.2:1b"]:
            if any(pref in m for m in models):
                # Find exact match
                for m in models:
                    if m.startswith(pref): return m
        return models[0] if models else None
    except Exception:
        return None


class BaseAgent:
    """Shared logic for all agents."""

    def __init__(self, name: str, system_prompt: str, db=None,
                 max_history: int = 15, backend: str = None, backend_model: str = None):
        self.name = name
        self.system_prompt = system_prompt
        self.db = db
        self.max_history = max_history
        # Per-student history: {student_id: [messages]}
        self.histories: dict[int, list[dict]] = {}

        # Backend setup
        if backend and backend_model:
            self._backend = backend
            self.model = backend_model
        else:
            self._backend, self.model = detect_backend()

        # Clients
        self._ollama_client = None
        if self._backend == "ollama" and OLLAMA_AVAILABLE:
            try:
                self._ollama_client = ollama.Client(host=OLLAMA_HOST)
            except Exception: self._backend = "offline"

        self._gemini_model = None
        if self._backend == "gemini" and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self._gemini_model = genai.GenerativeModel(
                    self.model,
                    system_instruction=self.system_prompt
                )
            except Exception: self._backend = "offline"

    def _get_history(self, student_id: int) -> list[dict]:
        if student_id not in self.histories:
            self.histories[student_id] = []
        return self.histories[student_id]

    def _build_messages(self, user_msg: str, context: str = "", student_id: int = None) -> list[dict]:
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        history = self._get_history(student_id)
        messages.extend(history[-self.max_history:])
        messages.append({"role": "user", "content": user_msg})
        return messages

    def _call_llm(self, messages: list[dict]) -> str:
        if self._backend == "gemini":
            return self._call_gemini(messages)
        if self._backend == "ollama":
            return self._call_ollama(messages)
        return self._offline_response(messages[-1]["content"])

    def _call_gemini(self, messages: list[dict]) -> str:
        try:
            gemini_history = []
            for msg in messages:
                if msg["role"] == "system" and msg["content"] != self.system_prompt:
                    gemini_history.append({"role": "user", "parts": [f"[System Context] {msg['content']}"]})
                    gemini_history.append({"role": "model", "parts": ["Understood."]})
                elif msg["role"] == "user":
                    gemini_history.append({"role": "user", "parts": [msg["content"]]})
                elif msg["role"] == "assistant":
                    gemini_history.append({"role": "model", "parts": [msg["content"]]})
            
            if gemini_history and gemini_history[-1]["role"] == "user":
                current = gemini_history.pop()
                chat = self._gemini_model.start_chat(history=gemini_history)
                return chat.send_message(current["parts"][0]).text
            return self._gemini_model.generate_content(messages[-1]["content"]).text
        except Exception as e:
            return f"⚠️ Gemini Error: {e}"

    def _call_ollama(self, messages: list[dict]) -> str:
        try:
            response = self._ollama_client.chat(model=self.model, messages=messages)
            return response["message"]["content"]
        except Exception as e:
            return f"⚠️ Ollama Error: {e}"

    def _offline_response(self, user_msg: str) -> str:
        return (f"🔌 [{self.name}] Offline.\nBuild more, learn more! 💪\n"
                "Key math/physics logic is still active via SymPy.")

    def chat(self, user_msg: str, context: str = "", student_id: int = 1) -> str:
        messages = self._build_messages(user_msg, context, student_id)
        response = self._call_llm(messages)

        history = self._get_history(student_id)
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": response})
        if len(history) > self.max_history * 2:
            self.histories[student_id] = history[-self.max_history * 2:]

        if self.db:
            try:
                self.db.log_interaction(
                    student_id=student_id,
                    agent=self.name, topic="chat",
                    user_input=user_msg[:500], agent_response=response[:500], result="ok"
                )
            except Exception: pass
            
        return response

    def reset_history(self, student_id: int):
        if student_id in self.histories:
            self.histories[student_id] = []
