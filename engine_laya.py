"""
engine_laya.py - System 1 Fast Decision & Tool Router powered by Laya.
Evaluates developer intents, tool actions, and task complexity in a single forward pass (~33ms).
"""

import time
import os
import warnings
from typing import Dict, Any, Optional

warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

try:
    from laya import Router
    LAYA_AVAILABLE = True
except ImportError:
    LAYA_AVAILABLE = False


CODING_TOOLS_SCHEMA = {
    # 1. Action / Tool to execute
    "action": {
        "type": "choice",
        "instructions": "What primary developer action or tool is requested?",
        "criteria": {
            "edit_code": "Writing code, modifying existing files, refactoring, fixing bugs, or implementing features",
            "inspect_files": "Viewing file contents, listing files, locating functions, or searching codebase",
            "run_command": "Running terminal commands, test suites, builds, git status/diff, or package installs",
            "generate_report": "Generating documentation, repository reports, docx/pdf exports, or code summaries",
            "explain": "Explaining concepts, reviewing architecture, answering questions, or debugging reasoning",
            "audit_debt": "Checking code bloat, removing dead code, applying YAGNI pruning, or Ponytail review"
        }
    },
    
    # 2. Context requirement (Boolean)
    "needs_repo_context": {
        "type": "noul",
        "instructions": "Does this request need reading files or repository search before answering?"
    },

    # 3. Complexity rating (1 to 3)
    "task_complexity": {
        "type": "score",
        "instructions": "How complex is this task?",
        "criteria": [
            "trivial one-line change, simple command, or quick question",
            "standard function edit, single file update, or targeted test fix",
            "multi-file change, complex architectural design, or heavy refactoring"
        ]
    }
}


class LayaRouterEngine:
    def __init__(self, default_lang: str = "english"):
        self.router: Optional[Any] = None
        self.is_ready = False
        self._init_router(default_lang)

    def _init_router(self, default_lang: str):
        if not LAYA_AVAILABLE:
            return

        try:
            # Preload ONLY English checkpoint so it never attempts to download
            # the multi-gigabyte multilingual/typed-decisions checkpoints over the web.
            self.router = Router(default=default_lang)
            self.router.preload(["english"])
            self.is_ready = True
        except Exception:
            # Fallback to standard lazy router
            try:
                self.router = Router(default=default_lang)
                self.is_ready = True
            except Exception:
                self.is_ready = False

    def route_request(self, user_prompt: str, current_file: str = "", cwd: str = "") -> Dict[str, Any]:
        """
        Runs System 1 evaluation over the prompt in ~33ms.
        Returns action, confidence, needs_context, complexity, and latency.
        """
        start_t = time.perf_counter()
        lower = user_prompt.lower()
        
        # Fast semantic override for report generation
        if any(k in lower for k in ["report", "docx", "export doc", "summarize repo"]):
            return {
                "action": "generate_report",
                "confidence": 0.98,
                "needs_context": True,
                "complexity": 1.0,
                "latency_ms": 1.0,
                "model_used": "semantic-fastpath",
                "raw": {}
            }

        state = {
            "body": user_prompt,
            "current_file": current_file or "none",
            "cwd": cwd or os.getcwd()
        }

        if self.is_ready and self.router:
            try:
                res = self.router.predict(state, CODING_TOOLS_SCHEMA)
                elapsed_ms = (time.perf_counter() - start_t) * 1000
                answers = res.get("answers", {})
                
                action_data = answers.get("action", {})
                action = action_data.get("choice", "explain")
                confidence = action_data.get("confidence", 0.85)
                
                needs_context_data = answers.get("needs_repo_context", {})
                needs_context = needs_context_data.get("answer", False)
                
                complexity_data = answers.get("task_complexity", {})
                complexity = complexity_data.get("score", 1.0)
                
                routing_info = res.get("routing", {})

                return {
                    "action": action,
                    "confidence": confidence,
                    "needs_context": needs_context,
                    "complexity": complexity,
                    "latency_ms": elapsed_ms,
                    "model_used": routing_info.get("model", "english"),
                    "raw": res
                }
            except Exception:
                pass

        # Fast fallback if Laya is offline
        elapsed_ms = (time.perf_counter() - start_t) * 1000
        if any(w in lower for w in ["run", "test", "pytest", "npm", "cargo", "git", "install"]):
            action = "run_command"
        elif any(w in lower for w in ["read", "find", "grep", "search", "where", "show"]):
            action = "inspect_files"
        elif any(w in lower for w in ["write", "create", "fix", "refactor", "implement", "edit"]):
            action = "edit_code"
        elif any(w in lower for w in ["yagni", "lazy", "bloat", "audit", "clean"]):
            action = "audit_debt"
        else:
            action = "explain"

        return {
            "action": action,
            "confidence": 0.80,
            "needs_context": ("file" in lower or "repo" in lower or "codebase" in lower),
            "complexity": 1.0,
            "latency_ms": elapsed_ms,
            "model_used": "heuristic-fallback",
            "raw": {}
        }
