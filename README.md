# Vredat (Verdeta) ⚡

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Ollama Compatible](https://img.shields.io/badge/Ollama-Local_Inference-brightgreen.svg)](https://ollama.ai)

> **Lightweight, Sub-50ms Neuro-Symbolic AI Coding Environment for the Terminal**

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          ⚡ ~33ms Intent Classification • 🧠 YAGNI Memory Ladder • 🔒 100% Local
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Vredat is a fast, terminal-first AI pair programmer powered by a **three-tier neuro-symbolic architecture**. Rather than wasting 3-5 seconds querying a massive cloud model just to decide what tool to use, Vredat classifies developer intent in a single **~33ms forward pass**, prunes conversation fluff using Dietrich Gebert's **Ponytail YAGNI ladder**, and streams code using local Ollama models.

---

## 🏗️ Architecture

```text
                       ┌──────────────────────────────────────────────┐
                       │          Developer Input / Terminal          │
                       │             "vredat" or "verdeta"            │
                       └──────────────────────┬───────────────────────┘
                                              │
                      ┌───────────────────────▼───────────────────────┐
                      │             Laya (System 1)                   │  ~33ms
                      │   - Fast Intent & Tool Classification         │
                      │   - Complexity Rating (1-3)                   │
                      │   - Repo Context Detection (Boolean)          │
                      └───────────────────────┬───────────────────────┘
                                              │
                      ┌───────────────────────▼───────────────────────┐
                      │       Ponytail Memory Manager                 │
                      │   - Context Token Compressor                  │
                      │   - YAGNI Senior Dev Ladder (Lite/Full/Ultra) │
                      │   - Project Decision Ledger (.vredat/)        │
                      └───────────────────────┬───────────────────────┘
                                              │
                         ┌────────────────────┴────────────────────┐
                         │                                         │
               [ Deterministic Tools ]                  [ System 2 Code Model ]
             (Terminal, Grep, Git, Diff)             (Llama 3.2 1B / Qwen 2.5 Coder)
              *Zero LLM compute needed*               *Real-time token streaming*
```

---

## ⚡ How It Works

1. **System 1 (Laya):**  
   Evaluates your prompt in a **single forward pass in ~33ms**. Instead of burning latency waiting for a large LLM, Laya instantly classifies the intent (`edit_code`, `inspect_files`, `run_command`, `explain`, `audit_debt`) and rates task complexity.
2. **Memory Management (Ponytail):**  
   Enforces Dietrich Gebert's **Ponytail Ladder**:
   * Rung 1: Does this need to exist? (YAGNI)
   * Rung 2: Already in this codebase?
   * Rung 3: Stdlib does it?
   * Rung 4: Native platform feature?
   * Rung 5: Existing dependency?
   * Rung 6: One line?
   * Rung 7: Minimum working code.
   Ponytail prunes conversational fluff, prevents context window overflow, and stores key architectural decisions in `.vredat/memory.json`.
3. **System 2 (Local LLM via Ollama):**  
   Streams high-quality code completions in real time using your local Ollama backend (default: `llama3.2:1b`, with support for `qwen2.5-coder:3b`, `qwen2.5-coder:1.5b-instruct`, etc.).

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure [Ollama](https://ollama.ai) is running locally and you have pulled a base coding model:
```bash
ollama pull llama3.2:1b
# or: ollama pull qwen2.5-coder:1.5b-instruct
```

### 2. Installation
```bash
git clone https://github.com/pranav520214/vredat.git
cd vredat

pip install -e .
```

### 3. Launch
Open any terminal (PowerShell, Command Prompt, macOS Terminal, Linux Bash) and type:
```bash
vredat
# (or)
verdeta
```

---

## ⌨️ Built-in Slash Commands

| Command | Action |
| :--- | :--- |
| `/help` | Show command cheat sheet |
| `/model <name>` | Switch active model (e.g. `/model llama3.2:1b` or `/model qwen2.5-coder:3b`) |
| `/models` | List all models installed in your local Ollama |
| `/ponytail <lite\|full\|ultra>` | Change Ponytail YAGNI intensity level |
| `/memory` | Inspect active memory ledger and recently touched files |
| `/clear` | Clear short-term chat context |
| `/status` | View system health and engine info |
| `/exit` | Exit the terminal environment |

---

## 📚 Documentation
* [System Architecture](docs/architecture.md): Deep-dive into the three-tier neuro-symbolic engine.
* [Execution Flows & Setup](docs/setup.md): Complete setup, pipeline sequence, and troubleshooting.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
