"""
cli.py - Main Interactive Terminal REPL for Vredat.
Combines Laya (System 1 Decision Engine), Ponytail (Memory & YAGNI Manager), and Local LLMs.
"""

import os
import sys

# Ensure UTF-8 output encoding on Windows consoles to prevent charmap UnicodeEncodeErrors
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from engine_laya import LayaRouterEngine
from memory_ponytail import PonytailMemoryManager
from engine_llm import LocalLLMEngine
import tools
import report_generator

console = Console(safe_box=True)

BANNER = """[bold cyan]====================================================[/bold cyan]
[bold cyan]           V R E D A T   C O D I N G   A I          [/bold cyan]
[dim]     Terminal AI Coding Environment (alias: verdeta) [/dim]
[bold cyan]====================================================[/bold cyan]"""

class VredatApp:
    def __init__(self, workspace_dir: str = ""):
        self.workspace_dir = workspace_dir or os.getcwd()
        self.console = console
        
        # 1. Initialize Ponytail Memory Manager
        self.memory = PonytailMemoryManager(workspace_dir=self.workspace_dir)
        
        # 2. Initialize Local LLM (prefer qwen2.5-coder:3b, qwen2.5-coder:1.5b-instruct, or llama3.2:1b)
        self.llm = LocalLLMEngine(preferred_model="qwen2.5-coder:3b")
        
        # 3. Initialize Laya Fast Router
        self.laya = LayaRouterEngine()

    def print_welcome(self):
        self.console.print(BANNER)
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("[bold yellow]System 1 Engine:[/bold yellow]", f"Laya ({'Ready' if self.laya.is_ready else 'Fallback Heuristic'}) [dim]~33ms[/dim]")
        table.add_row("[bold magenta]Memory Manager:[/bold magenta]", f"Ponytail [{self.memory.intensity.upper()}] [dim](YAGNI Ladder)[/dim]")
        table.add_row("[bold green]Local LLM Model:[/bold green]", f"{self.llm.active_model} [dim](via Ollama)[/dim]")
        table.add_row("[bold blue]Workspace Directory:[/bold blue]", f"{self.workspace_dir}")
        
        self.console.print(Panel(table, border_style="cyan", title="[bold white]System Status[/bold white]"))
        self.console.print("[dim]Commands: [bold]/help[/bold], [bold]/model[/bold], [bold]/report[/bold], [bold]/ponytail[/bold], [bold]/memory[/bold], [bold]/clear[/bold], [bold]/exit[/bold][/dim]\n")

    def handle_slash_command(self, cmd: str) -> bool:
        parts = cmd.strip().split()
        base = parts[0].lower()
        args = parts[1:]

        if base in ["/exit", "/quit", "/q"]:
            self.console.print("[yellow]Exiting Vredat. Happy coding![/yellow]")
            sys.exit(0)

        elif base == "/help":
            help_table = Table(title="Vredat Commands", border_style="cyan")
            help_table.add_column("Command", style="bold green")
            help_table.add_column("Description")
            help_table.add_row("/model <name>", "Switch model (e.g. /model qwen2.5-coder:3b or /model llama3.2:1b)")
            help_table.add_row("/models", "List all models available in local Ollama")
            help_table.add_row("/report [path]", "Generate comprehensive DOCX report of repository")
            help_table.add_row("/ponytail <lite|full|ultra>", "Set Ponytail YAGNI intensity level")
            help_table.add_row("/memory", "View active memory ledger & touched files")
            help_table.add_row("/clear", "Reset conversation context")
            help_table.add_row("/status", "Display current engines status")
            help_table.add_row("/exit", "Exit the terminal")
            self.console.print(help_table)
            return True

        elif base == "/models":
            models = self.llm.refresh_available_models()
            self.console.print(f"[bold]Available Models in Ollama:[/bold] {', '.join(models) if models else 'None found'}")
            return True

        elif base == "/model":
            if not args:
                self.console.print(f"Active model: [bold green]{self.llm.active_model}[/bold green]")
            else:
                target = args[0]
                if self.llm.set_model(target):
                    self.console.print(f"Switched model to: [bold green]{self.llm.active_model}[/bold green]")
                else:
                    self.console.print(f"[red]Model '{target}' not found in Ollama. Try /models to list.[/red]")
            return True

        elif base == "/report":
            out_file = args[0] if args else ""
            res = report_generator.create_repo_docx_report(self.workspace_dir, out_file)
            self.console.print(f"[bold green][Report Generated][/bold green] {res}")
            return True

        elif base == "/ponytail":
            if not args:
                self.console.print(f"Current Ponytail level: [bold magenta]{self.memory.intensity}[/bold magenta]")
            else:
                msg = self.memory.set_intensity(args[0])
                self.console.print(msg)
            return True

        elif base == "/memory":
            t = Table(title="Ponytail Memory & State Ledger", border_style="magenta")
            t.add_column("Key", style="bold yellow")
            t.add_column("Value")
            t.add_row("Intensity", self.memory.intensity)
            t.add_row("Conversation Turns", str(len(self.memory.history) // 2))
            t.add_row("Touched Files", ", ".join(self.memory.touched_files) if self.memory.touched_files else "None")
            t.add_row("Decisions Ledger", "\n".join(self.memory.decisions_ledger) if self.memory.decisions_ledger else "None")
            self.console.print(t)
            return True

        elif base == "/clear":
            self.memory.clear_session()
            self.console.print("[green]Session conversation cleared. Memory ledger preserved.[/green]")
            return True

        elif base == "/status":
            self.print_welcome()
            return True

        return False

    def _gather_repo_context(self, user_prompt: str) -> str:
        """Collects repository structure, files, and relevant contents."""
        lower = user_prompt.lower()
        context_parts = []

        # 1. Check for specific mentioned files
        words = user_prompt.split()
        for w in words:
            cleaned = w.strip("`'\" ,;()")
            target_path = os.path.join(self.workspace_dir, cleaned)
            if os.path.isfile(target_path):
                content = tools.view_file(target_path, max_lines=75)
                context_parts.append(f"--- File: {cleaned} ---\n{content}\n")
                if cleaned not in self.memory.touched_files:
                    self.memory.touched_files.append(cleaned)

        # 2. If general repo overview requested, scan repository
        if any(k in lower for k in ["repo", "project", "codebase", "architecture", "files", "directory", "report"]):
            meta = report_generator.scan_repository(self.workspace_dir)
            files_list = "\n".join(f"- {f['path']} ({f['lines']} lines, {f['size_kb']} KB)" for f in meta["files"])
            overview = f"""--- Current Repository Overview ({meta['repo_name']}) ---
Root: {meta['workspace_dir']}
Total files: {meta['total_files']} | Total lines: {meta['total_lines']}
Files:
{files_list}
"""
            context_parts.append(overview)

            # Include README if present
            readme_path = os.path.join(self.workspace_dir, "README.md")
            if os.path.isfile(readme_path):
                context_parts.append(f"--- README.md ---\n{tools.view_file(readme_path, max_lines=50)}\n")

        return "\n".join(context_parts)

    def process_prompt(self, user_prompt: str):
        # --- 1. LAYA SYSTEM 1 ROUTING (~33 ms) ---
        route = self.laya.route_request(user_prompt, cwd=self.workspace_dir)
        action = route["action"]
        confidence = route["confidence"]
        needs_context = route["needs_context"]
        complexity = route["complexity"]
        lat = route["latency_ms"]

        # Render Laya badge (ASCII safe)
        badge = f"[dim cyan][Laya {lat:.1f}ms]:[/dim cyan] [bold]{action}[/bold] [dim](conf: {confidence:.2f}, comp: {complexity:.1f}/3)[/dim]"
        self.console.print(badge)

        # --- 2. DETERMINISTIC SHORT-CIRCUIT: REPORT GENERATION ---
        if action == "generate_report" or any(k in user_prompt.lower() for k in ["report", "docx", "export doc"]):
            self.console.print(f"[bold green][Generating DOCX Report][/bold green] Scanning codebase and compiling metrics...")
            report_path = report_generator.create_repo_docx_report(self.workspace_dir)
            self.console.print(f"[bold cyan][Done] Report created:[/bold cyan] [bold underline]{report_path}[/bold underline]")
            self.memory.record_interaction(user_prompt, f"Generated repository report at {report_path}")
            return

        # --- 3. DETERMINISTIC SHORT-CIRCUIT: COMMAND EXECUTION ---
        if action == "run_command" and any(user_prompt.strip().startswith(p) for p in ["git", "pytest", "python", "npm", "cargo", "dir", "ls"]):
            self.console.print(f"[yellow]Executing terminal command directly...[/yellow]")
            output = tools.run_command(user_prompt, cwd=self.workspace_dir)
            self.console.print(Panel(output, title="Terminal Output", border_style="yellow"))
            self.memory.record_interaction(user_prompt, output)
            return

        # --- 4. CONTEXT GATHERING ---
        file_context = self._gather_repo_context(user_prompt)

        # --- 5. PONYTAIL MEMORY PRUNING & PROMPT ASSEMBLY ---
        messages = self.memory.get_optimized_messages(user_prompt, file_context=file_context)

        # --- 6. SYSTEM 2 STREAMING INFERENCE ---
        self.console.print(f"[dim green][LLM: {self.llm.active_model} streaming][/dim green]")
        
        full_response = []
        try:
            for chunk in self.llm.stream_chat(messages):
                full_response.append(chunk)
                sys.stdout.write(chunk)
                sys.stdout.flush()
            print() # newline
        except KeyboardInterrupt:
            self.console.print("\n[yellow][Interrupted by user][/yellow]")
            return

        response_str = "".join(full_response)
        
        # --- 7. RECORD INTERACTION IN PONYTAIL LEDGER ---
        self.memory.record_interaction(user_prompt, response_str)

    def run(self):
        self.print_welcome()
        while True:
            try:
                prompt_input = Prompt.ask("\n[bold cyan]vredat[/bold cyan]")
                if not prompt_input or not prompt_input.strip():
                    continue
                
                clean_input = prompt_input.strip()
                if clean_input.startswith("/"):
                    self.handle_slash_command(clean_input)
                    continue

                self.process_prompt(clean_input)

            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[yellow]Exiting Vredat. Bye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

def main():
    app = VredatApp()
    app.run()

if __name__ == "__main__":
    main()
