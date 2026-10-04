# Vredat (Verdeta) System Architecture

## 1. Three-Tier Neuro-Symbolic Model

Vredat solves the latency and context-bloat limitations of traditional AI coding assistants by splitting developer interaction into three decoupled layers:

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

## 2. Core Subsystems

### System 1: Laya Fast Classifier (`engine_laya.py`)
* Single-pass sub-50ms inference intent router.
* Categorizes developer requests into discrete intents:
  - `edit_code`: Modify source code in the repository.
  - `inspect_files`: Explore directory trees, search symbols.
  - `run_command`: Execute terminal shell commands.
  - `explain`: Answer architectural or technical queries.
  - `audit_debt`: Enforce YAGNI principles and scan dead code.

### Ponytail Memory Manager (`memory_ponytail.py`)
* Implements Dietrich Gebert's **Ponytail Ladder**:
  - Rung 1: Does this need to exist? (YAGNI)
  - Rung 2: Already in this codebase?
  - Rung 3: Stdlib does it?
  - Rung 4: Native platform feature?
  - Rung 5: Existing dependency?
  - Rung 6: One line?
  - Rung 7: Minimum working code.
* Compresses conversational history to prevent context window pollution.
* Persists key architectural decisions in `.vredat/memory.json`.

### System 2: Local Code LLM (`engine_llm.py`)
* Connects to local Ollama endpoints (streaming tokens in real time).
* Default base model: `llama3.2:1b`, with support for `qwen2.5-coder:1.5b-instruct` and `qwen2.5-coder:3b`.
