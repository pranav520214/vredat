# Vredat Execution Flows & Setup Runbook

## 1. Intent Routing & Execution Flow

```mermaid
flowchart TD
    A[Developer Prompt in Terminal] --> B[System 1 Laya Fast Classifier]
    B --> C{Task Complexity Rating}
    C -->|Level 1: Trivial Tool| D[Deterministic Tool Execution]
    D --> E[Terminal / Grep / Git Diff]
    E --> F[Direct Instant Terminal Response]
    C -->|Level 2 or 3: Synthesis| G[Ponytail Memory Manager]
    G --> H[YAGNI Ladder Evaluation]
    H --> I[Prune Context Fluff]
    I --> J[System 2 Local Ollama Stream]
    J --> K[Real-Time Token Stream to stdout]
    K --> L[Record Architectural Choice in .vredat/memory.json]
```

---

## 2. Setup Guide

### Prerequisites
* Python 3.10+
* [Ollama](https://ollama.ai) installed and running locally
* `ollama pull llama3.2:1b` (or `qwen2.5-coder:1.5b-instruct`)

```bash
# Clone repository
git clone https://github.com/pranav520214/vredat.git
cd vredat

# Install in editable mode
pip install -e .

# Launch Vredat from anywhere
vredat
```

---

## 3. Command Usage

```bash
# Interactive REPL mode:
vredat

# Single command execution:
vredat "find all TODO items in this repo"
vredat "refactor engine_llm.py to handle connection timeouts"

# Alias check:
verdeta --status
```
