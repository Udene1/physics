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

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from mistralai import Mistral as MistralClient
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False


# Hardware/Environment Config - Removed module globals for late-binding with .env
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def detect_backend() -> tuple[str, str]:
    """Auto-detect the best available LLM backend with free-tier safety."""
    target = os.environ.get("LLM_BACKEND", "auto").lower()
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    # Force Gemini
    if target == "gemini" and GEMINI_AVAILABLE and gemini_key:
        return "gemini", "gemini-3-flash-preview" # Latest power model
        
    # Force Ollama
    if target == "ollama" and OLLAMA_AVAILABLE:
        model = detect_model()
        if model: return "ollama", model
        
    # 1. Mistral Support (Promoted to Primary as requested)
    mistral_key = os.environ.get("MISTRAL_API_KEY")
    if MISTRAL_AVAILABLE and mistral_key:
        if target in ["auto", "mistral"]:
            return "mistral", "mistral-small-latest"

    # 2. Gemini Support
    if GEMINI_AVAILABLE and gemini_key:
        if target in ["auto", "gemini"]:
            # Using -latest aliases often resolves 404s on newer free-tier accounts
            return "gemini", "models/gemini-3-flash-preview"

    # 3. Groq Support (The LPU Llama-3-70b provider)
    groq_key = os.environ.get("GROQ_API_KEY")
    if target == "groq" and GROQ_AVAILABLE and groq_key:
        return "groq", "llama-3.1-70b-versatile"
        
    if GROQ_AVAILABLE and groq_key:
        return "groq", "llama-3.1-70b-versatile"
        
    if OLLAMA_AVAILABLE:
        try:
            client = ollama.Client(host=OLLAMA_HOST)
            models = client.list().get('models', [])
            if models:
                return "ollama", detect_model()
        except Exception:
            pass
            
    return "offline", "builtin"


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
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if self._backend == "gemini" and GEMINI_AVAILABLE and gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                # First attempt with requested model
                self._gemini_model = genai.GenerativeModel(
                    self.model,
                    system_instruction=self.system_prompt
                )
                # Verify immediately with a dummy call or ListModels
                # New: List available models to find a working alias if default fails
                try:
                    # Quick check: can we even see this model?
                    genai.get_model(self.model)
                except Exception as e:
                    print(f"DEBUG: {self.model} not found. Enumerating available models...")
                    try:
                        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                        flash_models = [m for m in available if 'flash' in m.lower()]
                        if flash_models:
                            new_model = flash_models[0]
                            print(f"DEBUG: Found valid model: {new_model}")
                            self.model = new_model
                            self._gemini_model = genai.GenerativeModel(
                                self.model,
                                system_instruction=self.system_prompt
                            )
                    except Exception:
                        print("WARNING: Could not enumerate Gemini models. Switching to offline.")
                        self._backend = "offline"
            except Exception as e:
                print(f"WARNING: Gemini Init failed: {e}")
                self._backend = "offline"

    def check_health(self) -> dict:
        """Check the status of the current backend for Edge resilience."""
        status = {"backend": self._backend, "model": self.model, "healthy": True}
        try:
            if self._backend == "gemini":
                # Dummy call or just check if model object exists
                if not self._gemini_model: status["healthy"] = False
            elif self._backend == "ollama":
                self._ollama_client.list()
            elif self._backend == "offline":
                status["healthy"] = True # Offline is always "healthy" in its own way
        except Exception:
            status["healthy"] = False
        return status

        self._groq_client = None
        groq_key = os.environ.get("GROQ_API_KEY")
        if self._backend == "groq" and GROQ_AVAILABLE and groq_key:
            try:
                # Set a reasonable timeout for Groq
                self._groq_client = Groq(api_key=groq_key, timeout=20.0)
            except Exception: self._backend = "offline"

        self._mistral_client = None
        mistral_key = os.environ.get("MISTRAL_API_KEY")
        if self._backend == "mistral" and MISTRAL_AVAILABLE and mistral_key:
            try:
                # Mistral client also supports timeout passing in complete()
                self._mistral_client = MistralClient(api_key=mistral_key)
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
        start_time = time.time()
        print(f"DEBUG: [{self.name}] Calling {self._backend} ({self.model})...")
        try:
            if self._backend == "gemini":
                res = self._call_gemini(messages)
            elif self._backend == "groq":
                res = self._call_groq(messages)
            elif self._backend == "mistral":
                res = self._call_mistral(messages)
            elif self._backend == "ollama":
                res = self._call_ollama(messages)
            else:
                res = self._offline_response(messages[-1]["content"])
            
            elapsed = time.time() - start_time
            print(f"DEBUG: [{self.name}] Response received in {elapsed:.2f}s")
            return res
        except Exception as e:
            print(f"ERROR: [{self.name}] LLM call crashed: {e}")
            return f"⚠️ Udene Brain encountered a technical glitch: {e}"

    def _call_gemini(self, messages: list[dict], attempt_lite: bool = True) -> str:
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
            
            # Simple content generation
            content = []
            for m in messages:
                if m.get("image"):
                    content.append(m["image"])
                content.append(m["content"])
                
            return self._gemini_model.generate_content(content).text
        except Exception as e:
            err_msg = str(e)
            
            # 404 / NotFound Fallback (New Keys sometimes mismatch on model names)
            if "404" in err_msg or "not found" in err_msg.lower():
                if attempt_lite:
                    for alt in ["models/gemini-1.5-flash", "gemini-1.5-flash", "models/gemini-1.5-flash-8b"]:
                        if alt == self.model: continue
                        print(f"DEBUG: Gemini 404. Probing {alt}...")
                        try:
                            alt_model = genai.GenerativeModel(alt)
                            return alt_model.generate_content(messages[-1]["content"]).text
                        except Exception: continue

            # Handle Quota / Resource Exhausted
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                if attempt_lite and "8b" not in self.model:
                    try:
                        lite_model = genai.GenerativeModel("models/gemini-1.5-flash-8b")
                        prompt = f"{self.system_prompt}\n\nLast Message: {messages[-1]['content']}"
                        return lite_model.generate_content(prompt).text
                    except Exception: pass
                return "⚠️ Udene Brain is resting (Free Tier Quota). Try again in 60 seconds! ⏳"
            
            if "403" in err_msg or "PERMISSION_DENIED" in err_msg:
                return "⚠️ Gemini API Key restriction. Please check your Google AI Studio settings. 🔐"
                
            return f"⚠️ Gemini Error: {err_msg}"

    def _call_groq(self, messages: list[dict]) -> str:
        if not self._groq_client:
            return self._offline_response(messages[-1]["content"])
        try:
            # Flatten messages for Groq format
            completion = self._groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg:
                return "⚠️ Groq LPU is busy. Switching back to Gemini logic... ⚡"
            return f"⚠️ Groq Error: {err_msg}"

    def _call_mistral(self, messages: list[dict]) -> str:
        if not self._mistral_client:
            return self._offline_response(messages[-1]["content"])
        try:
            # Mistral messages format is similar to OpenAI
            response = self._mistral_client.chat.complete(
                model=self.model,
                messages=messages,
                timeout_ms=20000 # 20 seconds
            )
            return response.choices[0].message.content
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg:
                return "⚠️ Mistral is cooling down. Falling back to next available backend... 🌬️"
            return f"⚠️ Mistral Error: {err_msg}"

    def _call_ollama(self, messages: list[dict]) -> str:
        if not self.model:
            return self._offline_response(messages[-1]["content"])
        try:
            # Set a 30-second timeout for local Ollama
            response = self._ollama_client.chat(
                model=self.model, 
                messages=messages,
                options={"timeout": 30}
            )
            return response["message"]["content"]
        except Exception as e:
            return f"⚠️ Ollama Error: {e} (Connection Timeout)"

    def _offline_response(self, user_msg: str) -> str:
        return (f"🔌 [{self.name}] Offline.\nBuild more, learn more! 💪\n"
                "Key math/physics logic is still active via SymPy.")

    def chat(self, user_msg: str, context: str = "", student_id: int = 1, image=None) -> str:
        messages = self._build_messages(user_msg, context, student_id)
        
        if image:
            # Store image in the last message if provided
            messages[-1]["image"] = image

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
                    agent=self.name, topic="vision_chat" if image else "chat",
                    user_input=user_msg[:500], agent_response=response[:500], result="ok"
                )
            except Exception: pass
            
        return response

    def reset_history(self, student_id: int):
        if student_id in self.histories:
            self.histories[student_id] = []

    def get_student_state(self, student_id: int) -> dict:
        """Fetch persistent agent state from DB."""
        if self.db:
            return self.db.get_agent_state(student_id, self.name)
        return {}
