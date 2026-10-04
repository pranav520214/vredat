"""
memory_ponytail.py - Ponytail Memory Manager & Lean Senior Dev Ruleset.
Prevents context window bloat, prunes conversational noise, and enforces YAGNI ladder.
Inspired by DietrichGebert/ponytail.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional

PONYTAIL_LADDER = """
# Ponytail: Lazy Senior Dev Rules (ACTIVE)
You are a senior developer who values simplicity, minimal diffs, and zero bloat.
The best code is the code never written.

## The Ladder (Stop at the first rung that works):
1. Does this need to exist at all? (YAGNI -> skip if speculative)
2. Already in this codebase? -> Reuse it, do not rewrite.
3. Stdlib does it? -> Use Python / platform standard library.
4. Native platform feature covers it? -> Use OS / browser / shell native.
5. Already-installed dependency solves it? -> Never add a new dependency.
6. Can it be one line? -> Make it one line.
7. Only then: The absolute minimum code that works.

## Output Constraints:
- Code first.
- At most two or three short lines explaining: what was skipped, and when to add it.
- Format: `[code] -> skipped: [X], add when [Y]`
- No unrequested boilerplate, no essays, no design tours.
- Never sacrifice: input validation, error handling, security, or data loss prevention.
"""

INTENSITY_INSTRUCTIONS = {
    "lite": "Ponytail Lite: Provide the requested implementation, but note the 1-line lazy/stdlib alternative if available.",
    "full": "Ponytail Full (Default): Strictly climb the ladder. Prefer stdlib and native features. Minimalist diffs only.",
    "ultra": "Ponytail Ultra: Extreme YAGNI. Favor deletion over addition. Question unneeded abstractions before writing."
}

class PonytailMemoryManager:
    def __init__(self, workspace_dir: str = "", intensity: str = "full", max_history_turns: int = 6):
        self.workspace_dir = workspace_dir or os.getcwd()
        self.intensity = intensity if intensity in INTENSITY_INSTRUCTIONS else "full"
        self.max_history_turns = max_history_turns
        self.memory_dir = os.path.join(self.workspace_dir, ".vredat")
        self.memory_file = os.path.join(self.memory_dir, "memory.json")
        
        # State ledger
        self.history: List[Dict[str, str]] = []
        self.touched_files: List[str] = []
        self.decisions_ledger: List[str] = []
        self._load_memory()

    def set_intensity(self, level: str) -> str:
        level = level.lower().strip()
        if level in INTENSITY_INSTRUCTIONS:
            self.intensity = level
            return f"Ponytail intensity set to: [bold green]{level}[/bold green]"
        return f"Unknown intensity '{level}'. Choose: lite, full, ultra"

    def _load_memory(self):
        """Loads persistent project-level memory ledger if available."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.touched_files = data.get("touched_files", [])[-20:]
                    self.decisions_ledger = data.get("decisions_ledger", [])[-15:]
            except Exception:
                pass

    def save_memory(self):
        """Persists the memory ledger to .vredat/memory.json."""
        try:
            os.makedirs(self.memory_dir, exist_ok=True)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump({
                    "touched_files": list(set(self.touched_files)),
                    "decisions_ledger": self.decisions_ledger[-20:],
                    "updated_at": time.time()
                }, f, indent=2)
        except Exception:
            pass

    def record_interaction(self, user_msg: str, assistant_msg: str, files_affected: Optional[List[str]] = None):
        """Records a conversation turn and keeps context lean."""
        # Prune older turns if history exceeds max
        self.history.append({"role": "user", "content": user_msg.strip()})
        self.history.append({"role": "assistant", "content": assistant_msg.strip()})
        
        if len(self.history) > self.max_history_turns * 2:
            # Drop older turns to keep token consumption minimal
            self.history = self.history[-(self.max_history_turns * 2):]

        if files_affected:
            for f in files_affected:
                if f not in self.touched_files:
                    self.touched_files.append(f)

        self.save_memory()

    def record_decision(self, decision: str):
        """Records an architectural or YAGNI decision."""
        if decision and decision not in self.decisions_ledger:
            self.decisions_ledger.append(decision)
            self.save_memory()

    def build_system_prompt(self, file_context: str = "") -> str:
        """
        Builds a compact, high-signal system prompt injecting Ponytail guidelines
        and current project memory ledger.
        """
        components = [
            PONYTAIL_LADDER,
            f"Active Intensity: {INTENSITY_INSTRUCTIONS[self.intensity]}"
        ]

        if self.decisions_ledger:
            ledger_text = "\n".join(f"- {d}" for d in self.decisions_ledger[-5:])
            components.append(f"\n## Project Decision Ledger (Memory):\n{ledger_text}")

        if self.touched_files:
            recent_files = ", ".join(self.touched_files[-5:])
            components.append(f"\n## Recently Touched Files:\n{recent_files}")

        if file_context:
            components.append(f"\n## Relevant File Context:\n{file_context}")

        return "\n\n".join(components)

    def get_optimized_messages(self, current_user_msg: str, file_context: str = "") -> List[Dict[str, str]]:
        """
        Returns the optimized message payload for Ollama/Llama.
        Prunes filler words and keeps context strictly minimal.
        """
        messages = [
            {"role": "system", "content": self.build_system_prompt(file_context)}
        ]

        # Add recent conversation turns
        for turn in self.history:
            messages.append(turn)

        # Add current user prompt
        messages.append({"role": "user", "content": current_user_msg.strip()})
        return messages

    def clear_session(self):
        """Clears short-term conversational history."""
        self.history.clear()
