"""
agents/agent_loop.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT LOOP PATTERN  —  Perceive → Think → Act → Observe  (repeat)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Each iteration:
  1. PERCEIVE  — collect environment state + memory context
  2. THINK     — LLM reasons about what to do next (tool or finish)
  3. ACT       — execute chosen tool
  4. OBSERVE   — record result, update world-state, loop or exit
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic

from config import settings
from memory.store import AgentMemory
from tools.base import ToolRegistry, ToolResult

logger = logging.getLogger("AgentLoop")


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class LoopStep:
    iteration: int
    phase: str          # perceive / think / act / observe
    content: Any
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RunResult:
    success: bool
    answer: str
    iterations: int
    steps: list[LoopStep]
    tool_calls: int
    elapsed_s: float
    error: str = ""


# ─── AgentLoop ────────────────────────────────────────────────────────────────

class AgentLoop:
    """
    Classic Perceive → Think → Act → Observe loop.

    Usage:
        registry = ToolRegistry().register(CalculatorTool()).register(...)
        agent = AgentLoop(registry)
        result = agent.run("What is 15% of the current Bitcoin price?")
        print(result.answer)
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        memory: AgentMemory | None = None,
        model: str | None = None,
        max_iterations: int | None = None,
        verbose: bool = True,
    ):
        settings.validate()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.registry = tool_registry
        self.memory = memory or AgentMemory("loop_agent")
        self.model = model or settings.model
        self.max_iter = max_iterations or settings.max_iterations
        self.verbose = verbose
        self._steps: list[LoopStep] = []

    # ── Public ─────────────────────────────────────────────────────────────────

    def run(self, goal: str) -> RunResult:
        """Execute the agent loop for the given goal."""
        t0 = time.time()
        self._steps = []
        self.memory.working.clear()
        tool_call_count = 0

        logger.info(f"[AgentLoop] Starting goal: {goal[:80]}")
        self._print_banner(goal)

        messages: list[dict] = [{"role": "user", "content": goal}]

        for iteration in range(1, self.max_iter + 1):

            # ── PHASE 1: PERCEIVE ───────────────────────────────────────────
            perception = self._perceive(goal, iteration)
            self._record(iteration, "perceive", perception)
            self._log("PERCEIVE", perception, "cyan")

            # ── PHASE 2: THINK (LLM call) ──────────────────────────────────
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=settings.max_tokens,
                    system=self._system_prompt(),
                    tools=self.registry.all_schemas(),
                    messages=messages,
                )
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return RunResult(False, "", iteration, self._steps, tool_call_count,
                                 time.time() - t0, str(e))

            thought = self._extract_text(response)
            self._record(iteration, "think", thought)
            self._log("THINK", thought or "(reasoning via tool selection)", "yellow")

            # ── PHASE 3: ACT ───────────────────────────────────────────────
            if response.stop_reason == "end_turn":
                # Agent decided it's done
                answer = thought or "(no text response)"
                self._record(iteration, "observe", {"done": True, "answer": answer})
                self._log("OBSERVE", f"Goal achieved in {iteration} iteration(s)", "green")
                self.memory.remember(f"goal: {goal[:60]}", f"success after {iteration} steps")
                elapsed = time.time() - t0
                self._print_summary(iteration, tool_call_count, elapsed)
                return RunResult(True, answer, iteration, self._steps, tool_call_count, elapsed)

            if response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    tool_name = block.name
                    tool_input = block.input
                    self._record(iteration, "act", {"tool": tool_name, "input": tool_input})
                    self._log("ACT", f"Tool: {tool_name}  Input: {json.dumps(tool_input)[:120]}", "magenta")

                    # Execute tool
                    result: ToolResult = self.registry.execute(tool_name, **tool_input)
                    tool_call_count += 1

                    # ── PHASE 4: OBSERVE ────────────────────────────────────
                    observation = result.to_str()
                    self._record(iteration, "observe", {"tool": tool_name, "result": observation[:300]})
                    self._log(
                        "OBSERVE",
                        f"[{'✓' if result.success else '✗'} {tool_name}]  {observation[:200]}",
                        "green" if result.success else "red",
                    )

                    self.memory.log(f"[iter {iteration}] {tool_name}: {observation[:100]}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": observation,
                    })

                # Feed results back → next iteration will PERCEIVE again
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

        # Max iterations reached
        return RunResult(False, "Max iterations reached.", self.max_iter,
                         self._steps, tool_call_count, time.time() - t0,
                         "max_iterations_exceeded")

    # ── Private helpers ────────────────────────────────────────────────────────

    def _perceive(self, goal: str, iteration: int) -> dict:
        """Collect current environment context."""
        return {
            "goal": goal,
            "iteration": iteration,
            "max_iterations": self.max_iter,
            "tools_available": self.registry.list_names(),
            "working_memory": self.memory.working_summary(),
        }

    def _system_prompt(self) -> str:
        past = self.memory.episodic.recall("agent task", n=3)
        past_str = "\n".join(f"  - {e['text'][:80]}" for e in past) or "  (none yet)"
        return f"""You are an intelligent AI agent running a Perceive→Think→Act→Observe loop.

At each iteration you:
1. PERCEIVE  — understand the current state and goal
2. THINK     — reason about what action to take next
3. ACT       — call a tool to make progress
4. OBSERVE   — the result is fed back and you loop again

Relevant past experience:
{past_str}

Rules:
- Use tools to gather information or take actions.
- When you have enough information to answer, stop using tools and provide your final answer.
- Be concise in your reasoning. Don't repeat yourself.
- If a tool fails, try an alternative approach."""

    @staticmethod
    def _extract_text(response) -> str:
        return " ".join(
            block.text for block in response.content if hasattr(block, "text")
        ).strip()

    def _record(self, iteration: int, phase: str, content: Any) -> None:
        self._steps.append(LoopStep(iteration, phase, content))

    def _log(self, label: str, msg: str, color: str = "white") -> None:
        if not self.verbose:
            return
        colors = {
            "cyan": "\033[96m", "yellow": "\033[93m", "magenta": "\033[95m",
            "green": "\033[92m", "red": "\033[91m", "white": "\033[97m",
        }
        reset = "\033[0m"
        c = colors.get(color, "")
        print(f"  {c}[{label:8s}]{reset} {str(msg)[:180]}")

    def _print_banner(self, goal: str) -> None:
        if not self.verbose:
            return
        w = 65
        print("\n" + "═" * w)
        print(f"  🔄  AGENT LOOP  —  Perceive → Think → Act → Observe")
        print("═" * w)
        print(f"  Goal : {goal[:w-10]}")
        print(f"  Model: {self.model}   Max-iter: {self.max_iter}")
        print("─" * w)

    def _print_summary(self, iters: int, calls: int, elapsed: float) -> None:
        if not self.verbose:
            return
        print("\n" + "─" * 65)
        print(f"  ✅ Done  —  {iters} iteration(s)  |  {calls} tool call(s)  |  {elapsed:.1f}s")
        print("═" * 65 + "\n")
