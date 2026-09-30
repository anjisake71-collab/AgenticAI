"""
tools/builtin.py
Built-in tools:  calculator, file_read, file_write, web_search, run_python
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

from .base import ToolBase


# ─── Calculator ───────────────────────────────────────────────────────────────

class CalculatorTool(ToolBase):
    name = "calculator"
    description = "Safely evaluate mathematical expressions and return the result."

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate, e.g. '(15 * 8) / 3 + 10'",
                }
            },
            "required": ["expression"],
        }

    def _run(self, expression: str) -> dict:
        allowed = set("0123456789+-*/.()% eE")
        if not all(c in allowed for c in expression):
            raise ValueError(f"Unsafe characters in expression: {expression}")
        result = eval(expression, {"__builtins__": {}})          # no builtins
        return {"expression": expression, "result": result}


# ─── File Read ────────────────────────────────────────────────────────────────

class FileReadTool(ToolBase):
    name = "file_read"
    description = "Read the contents of a file from the local filesystem."

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative or absolute file path"},
            },
            "required": ["path"],
        }

    def _run(self, path: str) -> dict:
        p = Path(path).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        content = p.read_text(encoding="utf-8")
        return {"path": str(p), "content": content, "lines": len(content.splitlines())}


# ─── File Write ───────────────────────────────────────────────────────────────

class FileWriteTool(ToolBase):
    name = "file_write"
    description = "Write or append content to a file on the local filesystem."

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write to"},
                "content": {"type": "string", "description": "Text content to write"},
                "mode": {
                    "type": "string",
                    "enum": ["write", "append"],
                    "description": "'write' overwrites, 'append' adds to end",
                    "default": "write",
                },
            },
            "required": ["path", "content"],
        }

    def _run(self, path: str, content: str, mode: str = "write") -> dict:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        file_mode = "a" if mode == "append" else "w"
        with open(p, file_mode, encoding="utf-8") as f:
            f.write(content)
        return {"path": str(p), "bytes_written": len(content.encode()), "mode": mode}


# ─── Web Search (Tavily) ──────────────────────────────────────────────────────

class WebSearchTool(ToolBase):
    name = "web_search"
    description = "Search the web for up-to-date information. Returns top results with titles, URLs and snippets."

    def __init__(self, api_key: str = ""):
        self._api_key = api_key or os.getenv("TAVILY_API_KEY", "")

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def _run(self, query: str, num_results: int = 5) -> dict:
        if not self._api_key:
            # Graceful fallback when no key available
            return {
                "query": query,
                "note": "No TAVILY_API_KEY set — returning mock result for demo",
                "results": [
                    {
                        "title": f"Mock result for: {query}",
                        "url": "https://example.com",
                        "snippet": f"This is a placeholder result for '{query}'. Set TAVILY_API_KEY in .env for real search.",
                    }
                ],
            }
        payload = {"api_key": self._api_key, "query": query, "max_results": num_results}
        resp = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            "query": query,
            "results": [
                {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content", "")[:400]}
                for r in data.get("results", [])
            ],
        }


# ─── Python Runner ────────────────────────────────────────────────────────────

class RunPythonTool(ToolBase):
    name = "run_python"
    description = "Execute a Python code snippet and return stdout/stderr. Timeout is 30 seconds."

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {
                    "type": "integer",
                    "description": "Max execution time in seconds (default 30)",
                    "default": 30,
                },
            },
            "required": ["code"],
        }

    def _run(self, code: str, timeout: int = 30) -> dict:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout,
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "return_code": result.returncode,
            "success": result.returncode == 0,
        }


# ─── List Files ───────────────────────────────────────────────────────────────

class ListFilesTool(ToolBase):
    name = "list_files"
    description = "List files and directories at a given path."

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list (default '.')",
                    "default": ".",
                }
            },
            "required": [],
        }

    def _run(self, path: str = ".") -> dict:
        p = Path(path).expanduser()
        if not p.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        entries = []
        for item in sorted(p.iterdir()):
            entries.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size_bytes": item.stat().st_size if item.is_file() else None,
            })
        return {"path": str(p), "entries": entries, "count": len(entries)}
