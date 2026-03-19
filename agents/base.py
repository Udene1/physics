"""
agents/base.py — Base agent class with dual LLM backend (Ollama local + Gemini cloud).

All specialized agents inherit from BaseAgent, which handles:
- LLM API communication with retry/fallback
- Conversation history management
- Automatic backend detection (Gemini > Ollama > offline)
"""

import os
import time
import json
from typing import Optional

# ── Backend: Ollama ───────────────────────────────────────────────
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# ── Backend: Gemini ───────────────────────────────────────────────
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Model preference order for Ollama (strong reasoning, CPU-friendly)
MODEL_PREFERENCE = [
    "qwen2.5:7b",
    "phi3.5:3.8b",
    "gemma2:2b",
    "deepseek-r1:1.5b",
    "llama3.2:1b",
    "qwen2.5:1.5b",
]

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
LLM_BACKEND = os.getenv("LLM_BACKEND", "auto")  # "auto", "gemini", "ollama"


def detect_backend() -> tuple[str, Optional[str]]:
    """
    Auto-detect the best available LLM backend.

    Returns (backend_type, model_name) where backend_type is 'gemini', 'ollama', or 'offline'.
    """
    if LLM_BACKEND == "gemini" or (LLM_BACKEND == "auto" and GEMINI_API_KEY):
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                return "gemini", GEMINI_MODEL
            except Exception:
                pass

    if LLM_BACKEND == "ollama" or LLM_BACKEND == "auto":
        model = _detect_ollama_model()
        if model:
            return "ollama", model

    # Fallback: try Gemini even if auto didn't prioritize it
    if GEMINI_AVAILABLE and GEMINI_API_KEY and LLM_BACKEND == "auto":
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            return "gemini", GEMINI_MODEL
        except Exception:
            pass

    return "offline", None


def _detect_ollama_model() -> Optional[str]:
    """Auto-detect the best available Ollama model."""
    if not OLLAMA_AVAILABLE:
        return None
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        available = client.list()
        model_names = [m.model for m in available.models] if available.models else []

        for preferred in MODEL_PREFERENCE:
            prefix = preferred.split(":")[0]
            for available_name in model_names:
                if available_name.startswith(prefix):
                    return available_name

        if model_names:
            return model_names[0]
        return None
    except Exception:
        return None


# Keep old name for backward compatibility
def detect_model() -> Optional[str]:
    """Legacy function — returns Ollama model name or None."""
    return _detect_ollama_model()


class BaseAgent:
    """
    Base class for all learning companion agents.

    Supports dual LLM backends: Ollama (local) and Gemini (cloud).
    """

    def __init__(self, name: str, system_prompt: str, db=None, model: str = None,
                 max_history: int = 20, backend: str = None, backend_model: str = None):
        self.name = name
        self.system_prompt = system_prompt
        self.db = db
        self.max_history = max_history
        self.history: list[dict] = []

        # Determine backend
        if backend and backend_model:
            self._backend = backend
            self.model = backend_model
        elif model:
            # Legacy: model string passed = Ollama
            self._backend = "ollama"
            self.model = model
        else:
            self._backend = "offline"
            self.model = None

        # Initialize Ollama client if needed
        self._ollama_client = None
        if self._backend == "ollama" and OLLAMA_AVAILABLE:
            try:
                self._ollama_client = ollama.Client(host=OLLAMA_HOST)
                self._ollama_client.list()
            except Exception:
                self._backend = "offline"

        # Initialize Gemini model if needed
        self._gemini_model = None
        if self._backend == "gemini" and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self._gemini_model = genai.GenerativeModel(
                    self.model,
                    system_instruction=self.system_prompt,
                )
            except Exception:
                self._backend = "offline"

    @property
    def is_online(self) -> bool:
        return self._backend in ("gemini", "ollama")

    @property
    def backend_info(self) -> str:
        if self._backend == "gemini":
            return f"Gemini ({self.model})"
        elif self._backend == "ollama":
            return f"Ollama ({self.model})"
        return "Offline"

    def _build_messages(self, user_msg: str, extra_context: str = "") -> list[dict]:
        """Build the message list for LLM API calls."""
        messages = [{"role": "system", "content": self.system_prompt}]

        if extra_context:
            messages.append({
                "role": "system",
                "content": f"Current context:\n{extra_context}"
            })

        messages.extend(self.history[-self.max_history:])
        messages.append({"role": "user", "content": user_msg})
        return messages

    def _call_llm(self, messages: list[dict], retries: int = 2) -> str:
        """Call the configured LLM backend with retry logic."""
        if self._backend == "gemini":
            return self._call_gemini(messages, retries)
        elif self._backend == "ollama":
            return self._call_ollama(messages, retries)
        else:
            return self._offline_response(messages[-1]["content"])

    def _call_gemini(self, messages: list[dict], retries: int = 2) -> str:
        """Call Google Gemini API."""
        for attempt in range(retries + 1):
            try:
                # Convert messages to Gemini format (skip system — it's in system_instruction)
                gemini_history = []
                for msg in messages:
                    if msg["role"] == "system":
                        # Add system context as user message for context
                        if msg["content"] != self.system_prompt:
                            gemini_history.append({
                                "role": "user",
                                "parts": [f"[Context] {msg['content']}"]
                            })
                            gemini_history.append({
                                "role": "model",
                                "parts": ["Understood, I'll use this context."]
                            })
                    elif msg["role"] == "user":
                        gemini_history.append({"role": "user", "parts": [msg["content"]]})
                    elif msg["role"] == "assistant":
                        gemini_history.append({"role": "model", "parts": [msg["content"]]})

                # Last message is the user's current input
                if gemini_history and gemini_history[-1]["role"] == "user":
                    current_msg = gemini_history.pop()
                    chat = self._gemini_model.start_chat(history=gemini_history)
                    response = chat.send_message(current_msg["parts"][0])
                    return response.text
                else:
                    response = self._gemini_model.generate_content(messages[-1]["content"])
                    return response.text

            except Exception as e:
                if attempt < retries:
                    time.sleep(1)
                    continue
                return (
                    f"⚠️ Gemini API error (attempt {attempt + 1}): {e}\n\n"
                    f"I can still help with math verification and progress tracking!"
                )

    def _call_ollama(self, messages: list[dict], retries: int = 2) -> str:
        """Call Ollama chat API with retry logic."""
        for attempt in range(retries + 1):
            try:
                response = self._ollama_client.chat(
                    model=self.model,
                    messages=messages,
                    options={"temperature": 0.7, "num_predict": 1024},
                )
                return response["message"]["content"]
            except Exception as e:
                if attempt < retries:
                    time.sleep(1)
                    continue
                return (
                    f"⚠️ Ollama error (attempt {attempt + 1}): {e}\n\n"
                    f"I can still help with math verification and progress tracking!"
                )

    def _offline_response(self, user_msg: str) -> str:
        """Fallback response when no LLM is available."""
        return (
            f"🔌 [{self.name}] I'm currently offline (no LLM connection).\n\n"
            f"I can still help you with:\n"
            f"  • Math problem verification (using SymPy)\n"
            f"  • Practice problem generation\n"
            f"  • Progress tracking and reports\n\n"
            f"Set GEMINI_API_KEY env var or start Ollama to unlock full tutoring!"
        )

    def chat(self, user_msg: str, context: str = "") -> str:
        """
        Main chat method — sends user message through LLM with context.
        """
        messages = self._build_messages(user_msg, context)
        response = self._call_llm(messages)

        self.history.append({"role": "user", "content": user_msg})
        self.history.append({"role": "assistant", "content": response})

        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]

        if self.db:
            try:
                self.db.log_interaction(
                    agent=self.name, topic="general",
                    user_input=user_msg[:500], agent_response=response[:500], result="ok",
                )
            except Exception:
                pass

        return response

    def reset_history(self):
        """Clear conversation history for this agent."""
        self.history.clear()
