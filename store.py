"""
store.py - Durable SQLite WAL State Store for Vredat.
Tracks tasks, execution DAG, episodic attempts, failures, and architectural decisions.
"""

import sqlite3
import os
import json
import time
from typing import List, Dict, Any, Optional

class VredatStore:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.db_dir = os.path.join(workspace_root, ".vredat")
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "vredat_state.sqlite3")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._configure_db()
        self._init_tables()

    def _configure_db(self):
        """Configures SQLite for maximum durability, speed, and concurrency."""
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA cache_size=-10000;") # Limit to ~10MB memory
        self.conn.execute("PRAGMA foreign_keys=ON;")

    def _init_tables(self):
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    target_files TEXT NOT NULL, -- JSON array of file paths
                    test_command TEXT NOT NULL,
                    status TEXT CHECK(status IN ('QUEUED', 'RUNNING', 'VERIFYING', 'BLOCKED', 'COMPLETED')) DEFAULT 'QUEUED',
                    complexity REAL DEFAULT 1.0,
                    assigned_model TEXT DEFAULT 'qwen2.5-coder:3b',
                    attempts INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS task_dependencies (
                    task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
                    depends_on_task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
                    PRIMARY KEY (task_id, depends_on_task_id)
                );

                CREATE TABLE IF NOT EXISTS episodic_attempts (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
                    attempt_number INTEGER NOT NULL,
                    model_used TEXT NOT NULL,
                    diff_applied TEXT,
                    test_exit_code INTEGER,
                    stdout_snippet TEXT,
                    stderr_snippet TEXT,
                    laya_diagnosis TEXT,
                    resolution_action TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS decisions_ledger (
                    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    title TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    alternatives TEXT, -- JSON array
                    made_by TEXT DEFAULT 'LAYA',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def add_task(self, task_id: str, title: str, description: str, target_files: List[str], 
                 test_command: str = "pytest", dependencies: Optional[List[str]] = None,
                 complexity: float = 1.0, model: str = "qwen2.5-coder:3b") -> str:
        """Adds a task to the execution queue."""
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO tasks 
                (task_id, title, description, target_files, test_command, status, complexity, assigned_model, attempts)
                VALUES (?, ?, ?, ?, ?, 'QUEUED', ?, ?, 0)
            """, (task_id, title, description, json.dumps(target_files), test_command, complexity, model))

            if dependencies:
                for dep in dependencies:
                    self.conn.execute("""
                        INSERT OR IGNORE INTO task_dependencies (task_id, depends_on_task_id)
                        VALUES (?, ?)
                    """, (task_id, dep))
        return task_id

    def get_next_runnable_task(self) -> Optional[Dict[str, Any]]:
        """Finds the next QUEUED task whose dependencies are all COMPLETED."""
        cursor = self.conn.cursor()
        query = """
            SELECT t.task_id, t.title, t.description, t.target_files, t.test_command, 
                   t.complexity, t.assigned_model, t.attempts, t.max_attempts
            FROM tasks t
            WHERE t.status = 'QUEUED'
              AND NOT EXISTS (
                  SELECT 1 FROM task_dependencies td
                  JOIN tasks parent ON td.depends_on_task_id = parent.task_id
                  WHERE td.task_id = t.task_id AND parent.status != 'COMPLETED'
              )
            ORDER BY t.created_at ASC
            LIMIT 1;
        """
        row = cursor.execute(query).fetchone()
        if not row:
            return None

        return {
            "task_id": row[0],
            "title": row[1],
            "description": row[2],
            "target_files": json.loads(row[3]),
            "test_command": row[4],
            "complexity": row[5],
            "assigned_model": row[6],
            "attempts": row[7],
            "max_attempts": row[8]
        }

    def update_task_status(self, task_id: str, status: str, attempts: Optional[int] = None):
        """Updates status of a task."""
        with self.conn:
            if attempts is not None:
                self.conn.execute("""
                    UPDATE tasks SET status = ?, attempts = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                """, (status, attempts, task_id))
            else:
                self.conn.execute("""
                    UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                """, (status, task_id))

    def record_attempt(self, task_id: str, attempt_num: int, model: str, diff: str,
                       exit_code: int, stdout: str, stderr: str, laya_diagnosis: str, resolution: str):
        """Records an episodic failure or success attempt."""
        with self.conn:
            self.conn.execute("""
                INSERT INTO episodic_attempts 
                (task_id, attempt_number, model_used, diff_applied, test_exit_code, 
                 stdout_snippet, stderr_snippet, laya_diagnosis, resolution_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (task_id, attempt_num, model, diff[:4000], exit_code, 
                  stdout[:1000], stderr[:1000], laya_diagnosis, resolution))

    def get_task_summary(self) -> Dict[str, Any]:
        """Returns counts of tasks in each status."""
        cursor = self.conn.cursor()
        rows = cursor.execute("SELECT status, count(*) FROM tasks GROUP BY status").fetchall()
        summary = {"QUEUED": 0, "RUNNING": 0, "COMPLETED": 0, "BLOCKED": 0}
        for st, count in rows:
            summary[st] = count
        return summary

    def list_all_tasks(self) -> List[Dict[str, Any]]:
        """Returns all tasks in order."""
        cursor = self.conn.cursor()
        rows = cursor.execute("SELECT task_id, title, status, attempts, assigned_model FROM tasks ORDER BY created_at ASC").fetchall()
        return [{"task_id": r[0], "title": r[1], "status": r[2], "attempts": r[3], "model": r[4]} for r in rows]
