"""
tools/base.py
Base tool class + registry — every tool inherits from ToolBase.
"""
from __future__ import annotations
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    output: Any
    error: str = ""
    latency_ms: float = 0.0

    def to_str(self) -> str:
        if self.success:
            return json.dumps(self.output, indent=2) if isinstance(self.output, dict) else str(self.output)
        return f"[ERROR] {self.error}"


class ToolBase(ABC):
    """Every tool inherits this. Provides schema + safe execution."""

    name: str = ""
    description: str = ""

    @property
    @abstractmethod
    def schema(self) -> dict:
        """Return Anthropic-compatible tool schema (input_schema)."""
        ...

    @abstractmethod
    def _run(self, **kwargs) -> Any:
        """Core tool logic — implement in subclass."""
        ...

    def run(self, **kwargs) -> ToolResult:
        """Safe wrapper with timing and error capture."""
        t0 = time.time()
        try:
            output = self._run(**kwargs)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                latency_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=str(e),
                latency_ms=(time.time() - t0) * 1000,
            )

    def to_api_schema(self) -> dict:
        """Format for Anthropic tools= parameter."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.schema,
        }


class ToolRegistry:
    """Central registry — register once, use everywhere."""

    def __init__(self):
        self._tools: dict[str, ToolBase] = {}

    def register(self, tool: ToolBase) -> "ToolRegistry":
        self._tools[tool.name] = tool
        return self  # chainable

    def get(self, name: str) -> ToolBase | None:
        return self._tools.get(name)

    def all_schemas(self) -> list[dict]:
        return [t.to_api_schema() for t in self._tools.values()]

    def execute(self, name: str, **kwargs) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(name, False, None, f"Tool '{name}' not found")
        return tool.run(**kwargs)

    def list_names(self) -> list[str]:
        return list(self._tools.keys())
