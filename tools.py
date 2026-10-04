"""
tools.py - Deterministic developer tools for Vredat.
Executes file reads, search, terminal commands, and git operations without LLM overhead.
"""

import os
import subprocess
import glob
from typing import List, Dict, Any, Optional

def view_file(filepath: str, max_lines: int = 150) -> str:
    """Reads content of a file."""
    if not os.path.exists(filepath):
        return f"[File not found: {filepath}]"
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        if len(lines) > max_lines:
            content = "".join(lines[:max_lines])
            content += f"\n... [Truncated: showing first {max_lines} of {len(lines)} lines]"
            return content
        return "".join(lines)
    except Exception as e:
        return f"[Error reading file: {e}]"

def write_file(filepath: str, content: str) -> str:
    """Writes content to a file, creating parent directories if needed."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"[Error writing file: {e}]"

def list_files(directory: str = ".", pattern: str = "*", recursive: bool = False) -> List[str]:
    """Lists files in the target directory."""
    try:
        if recursive:
            search_path = os.path.join(directory, "**", pattern)
            return [f for f in glob.glob(search_path, recursive=True) if os.path.isfile(f)][:50]
        else:
            search_path = os.path.join(directory, pattern)
            return [f for f in glob.glob(search_path) if os.path.isfile(f)][:50]
    except Exception:
        return []

def search_code(query: str, directory: str = ".") -> str:
    """Fast grep/search for a keyword in local files."""
    results = []
    # Ignore common noisy directories
    ignore_dirs = {".git", ".venv", "node_modules", "__pycache__", ".vredat"}
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in [".py", ".js", ".ts", ".html", ".css", ".md", ".json", ".rs", ".go", ".c", ".cpp"]:
                fp = os.path.join(root, file)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f, 1):
                            if query.lower() in line.lower():
                                rel_path = os.path.relpath(fp, directory)
                                results.append(f"{rel_path}:{idx}: {line.strip()[:100]}")
                                if len(results) >= 15:
                                    return "\n".join(results)
                except Exception:
                    pass
    return "\n".join(results) if results else "[No matches found]"

def run_command(command: str, cwd: str = "") -> str:
    """Executes a terminal command safely in the current workspace."""
    try:
        res = subprocess.run(
            command,
            shell=True,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            timeout=30
        )
        out = res.stdout
        err = res.stderr
        combined = []
        if out:
            combined.append(out.strip())
        if err:
            combined.append(f"[stderr]:\n{err.strip()}")
        return "\n".join(combined) if combined else "[Command completed with no output]"
    except subprocess.TimeoutExpired:
        return "[Error: Command timed out after 30 seconds]"
    except Exception as e:
        return f"[Execution error: {e}]"

def git_status(cwd: str = "") -> str:
    """Returns concise git status."""
    return run_command("git status --short", cwd=cwd)
