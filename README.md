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

### 5. Run
```bash
python main.py
```

## 🤖 Agents

| Agent | Role | Key Features |
|-------|------|-------------|
| 🌟 **Companion** | Daily motivator & goal setter | Nigerian-flavored encouragement, progress review, micro-goals |
| 📐 **Math Tutor** | Socratic math teacher | SymPy verification, problem generation, step-by-step hints |
| ⚛️ **Physics Supervisor** | Strict curriculum enforcer | Prerequisite gates, mastery tracking (0-100%), study plans |
| 🔧 **Hardware Bridge** | Practical build advisor | Nigeria-priced components, Arduino/Python code, impact framing |
| 📊 **Progress Tracker** | Record keeper & analyst | SQLite persistence, reports, session artifacts |

## 📚 Commands

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
├── main.py                    # Entry point & orchestrator
├── requirements.txt           # Dependencies
├── agents/
│   ├── base.py               # Base agent + Ollama client
│   ├── companion.py          # Daily Companion Agent
│   ├── math_tutor.py         # Math Tutor Agent
│   ├── physics_supervisor.py # Physics Supervisor Agent
│   ├── hardware_bridge.py    # Hardware Bridge Agent
│   └── progress_tracker.py   # Progress Tracker Agent
├── tools/
│   ├── math_verifier.py      # SymPy answer verification
│   ├── problem_generator.py  # Practice problem templates
│   └── progress_db.py        # SQLite progress database
├── integrations/
│   ├── telegram_bot.py       # Optional Telegram reminders
│   └── web_ui.py             # Optional Gradio web UI
└── memory/
    └── progress.db            # Created at runtime
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

## 🌍 Vision

Every formula learned, every circuit built, every concept mastered — is a step toward building devices that improve lives. From soil moisture sensors for farmers to temperature loggers for clinics, this system connects learning to real-world impact.

*Built with love for learners everywhere, especially in Benin City, Nigeria.* 🇳🇬
