"""
agents/base.py — Base agent class with Ollama LLM backend.

All specialized agents inherit from BaseAgent, which handles:
- Ollama API communication with retry/fallback
- Conversation history management
- Model auto-detection
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

# Model preference order (strong reasoning, CPU-friendly)
MODEL_PREFERENCE = [
    "qwen2.5:7b",
    "phi3.5:3.8b",
    "gemma2:2b",
    "deepseek-r1:1.5b",
    "llama3.2:1b",
    "qwen2.5:1.5b",
]

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def detect_model() -> Optional[str]:
    """Auto-detect the best available Ollama model."""
    if not OLLAMA_AVAILABLE:
        return None
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        available = client.list()
        model_names = [m.model for m in available.models] if available.models else []

        # Match by prefix (e.g., "qwen2.5:7b" matches "qwen2.5:7b-instruct-...")
        for preferred in MODEL_PREFERENCE:
            prefix = preferred.split(":")[0]
            for available_name in model_names:
                if available_name.startswith(prefix):
                    return available_name

        # Fall back to first available model
        if model_names:
            return model_names[0]

        return None
    except Exception:
        return None


class BaseAgent:
    """
    Base class for all learning companion agents.

    Manages conversation history, Ollama API calls, and retry logic.
    """

    def __init__(self, name: str, system_prompt: str, db=None, model: str = None,
                 max_history: int = 20):
        self.name = name
        self.system_prompt = system_prompt
        self.db = db
        self.model = model
        self.max_history = max_history
        self.history: list[dict] = []
        self._client = None
        self._ollama_ok = False

        if OLLAMA_AVAILABLE:
            try:
                self._client = ollama.Client(host=OLLAMA_HOST)
                self._client.list()  # Connection test
                self._ollama_ok = True
            except Exception:
                self._ollama_ok = False

    @property
    def is_online(self) -> bool:
        return self._ollama_ok and self.model is not None

    def _build_messages(self, user_msg: str, extra_context: str = "") -> list[dict]:
        """Build the message list for the Ollama API call."""
        messages = [{"role": "system", "content": self.system_prompt}]

        if extra_context:
            messages.append({
                "role": "system",
                "content": f"Current context:\n{extra_context}"
            })

        # Add conversation history (trimmed)
        messages.extend(self.history[-self.max_history:])

        messages.append({"role": "user", "content": user_msg})
        return messages

    def _call_ollama(self, messages: list[dict], retries: int = 2) -> str:
        """Call Ollama chat API with retry logic."""
        if not self.is_online:
            return self._offline_response(messages[-1]["content"])

        for attempt in range(retries + 1):
            try:
                response = self._client.chat(
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
                    f"⚠️ I'm having trouble connecting to the LLM (attempt {attempt + 1}). "
                    f"Error: {e}\n\n"
                    f"I can still help with math verification and progress tracking offline!"
                )

    def _offline_response(self, user_msg: str) -> str:
        """Fallback response when Ollama is not available."""
        return (
            f"🔌 [{self.name}] I'm currently offline (no LLM connection).\n\n"
            f"I can still help you with:\n"
            f"  • Math problem verification (using SymPy)\n"
            f"  • Practice problem generation\n"
            f"  • Progress tracking and reports\n\n"
            f"Start Ollama with a model to unlock full tutoring!\n"
            f"  → ollama pull qwen2.5:7b && ollama serve"
        )

    def chat(self, user_msg: str, context: str = "") -> str:
        """
        Main chat method — sends user message through LLM with context.

        Args:
            user_msg: The user's message.
            context: Additional context string (mastery, recent progress, etc.)

        Returns:
            Agent's response string.
        """
        messages = self._build_messages(user_msg, context)
        response = self._call_ollama(messages)

        # Update conversation history
        self.history.append({"role": "user", "content": user_msg})
        self.history.append({"role": "assistant", "content": response})

        # Trim history if needed
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]

        # Log interaction if DB is available
        if self.db:
            try:
                self.db.log_interaction(
                    agent=self.name,
                    topic="general",
                    user_input=user_msg[:500],
                    agent_response=response[:500],
                    result="ok",
                )
            except Exception:
                pass

        return response

    def reset_history(self):
        """Clear conversation history for this agent."""
        self.history.clear()
