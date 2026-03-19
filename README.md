# 🧠 AI Learning Companion

**A local-first, multi-agent AI system for self-teaching advanced mathematics, university-level physics, and practical hardware/electronics building.**

Built with the vision of deep conceptual understanding → real-world hardware creation → improving human lives (low-cost sensors/devices for agriculture, energy, health in resource-limited settings).

## 🚀 Quick Start

### 1. Install Python 3.10+
Download from [python.org](https://www.python.org/downloads/) if not already installed.

### 2. Install Ollama
```bash
# Windows: Download from https://ollama.com/download
# Linux:
curl -fsSL https://ollama.com/install.sh | sh
```

### 3. Pull a Model
```bash
# Recommended (best quality, needs ~4GB RAM):
ollama pull qwen2.5:7b

# Lighter alternatives:
ollama pull gemma2:2b       # ~2GB RAM
ollama pull llama3.2:1b     # ~1GB RAM
```

### 4. Install Dependencies
```bash
cd physics
pip install -r requirements.txt
```

### 🌐 Web App (Flask)

The system includes a premium dark-mode web interface, perfect for deployment or local browser use.

### Local Run
```bash
python app.py
# Opens at http://127.0.0.1:5000
```

### ☁️ Cloud Deployment (pxxl.app / Heroku)
The app is pre-configured for **pxxl.app** or any platform using a `Procfile`.

1.  **Get a Gemini API Key**: [Google AI Studio](https://aistudio.google.com/)
2.  **Set Environment Variables** on your hosting platform:
    -   `GEMINI_API_KEY`: Your Google API key
    -   `LLM_BACKEND`: `gemini` (forces cloud mode)
3.  **Deploy**: Push your repository to GitHub and connect it to pxxl.app.

## 🤖 Agents

| Agent | Role | Key Features |
|-------|------|-------------|
| 🌟 **Companion** | Daily motivator & goal setter | Nigerian-flavored encouragement, progress review, micro-goals |
| 📐 **Math Tutor** | Socratic math teacher | SymPy verification, problem generation, step-by-step hints |
| ⚛️ **Physics Supervisor** | Strict curriculum enforcer | Prerequisite gates, mastery tracking (0-100%), study plans |
| 🔧 **Hardware Bridge** | Practical build advisor | Nigeria-priced components, Arduino/Python code, impact framing |
| 📊 **Progress Tracker** | Record keeper & analyst | SQLite persistence, reports, session artifacts |

## 📚 Commands

Available in both CLI and Web App:

### Math & Practice
```
/problems <topic> [difficulty] [count]  — Generate practice problems
/verify <answer>                        — Check your answer
/hint                                   — Get a hint
/next                                   — Skip to next problem
```

**Topics:** `algebra`, `trigonometry`, `calculus`, `linear_algebra`, `differential_equations`, `physics_mechanics`

### Physics
```
/curriculum     — View full physics curriculum with progress
/study <topic>  — Get study plan for a topic
/prereq <topic> — Check prerequisites
```

### Hardware
```
/builds         — List all hardware projects
/build <name>   — Get project details
```

### Progress
```
/report   — View progress report
/weekly   — Weekly summary
/goals    — View pending goals
```

## 🏗️ Project Structure

```
physics/
├── app.py                     # Flask web server
├── main.py                    # CLI orchestrator & shared logic
├── requirements.txt           # Dependencies (Flask + Gemini + Ollama)
├── agents/
│   ├── base.py               # Dual Backend (Gemini/Ollama) client
│   └── ...                   # Specialized agents
├── tools/
│   └── ...                   # Math/Physics/DB tools
├── templates/
│   └── index.html            # Premium Chat UI
├── static/
│   ├── css/style.css         # Dark-mode styling
│   └── js/chat.js            # Frontend interactivity
├── Procfile                   # pxxl.app deployment config
└── runtime.txt                # Python version config
```

## 🌐 Optional: Web UI

```bash
pip install gradio
python -m integrations.web_ui
# Opens at http://127.0.0.1:7860
```

## 📱 Optional: Telegram Reminders

```bash
pip install requests
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

## 🔌 Offline Mode

The system works without internet after initial Ollama setup:
- **With Ollama:** Full AI tutoring, Socratic questioning, explanations
- **Without Ollama:** Math verification (SymPy), problem generation, progress tracking

## 🔌 LLM Backends

The system automatically detects the best available backend:
1.  **Gemini (Cloud)**: Uses `GEMINI_API_KEY` env var. Fast, free, and works on pxxl.app.
2.  **Ollama (Local)**: Uses local running models. Best for offline use.
3.  **Offline**: No AI chat, but math tools and progress tracking still work!

## 🌍 Vision

Every formula learned, every circuit built, every concept mastered — is a step toward building devices that improve lives. From soil moisture sensors for farmers to temperature loggers for clinics, this system connects learning to real-world impact.

*Built with love for learners everywhere, especially in Benin City, Nigeria.* 🇳🇬
