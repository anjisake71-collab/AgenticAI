"""
agents/react_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ReAct PATTERN  —  Thought → Action → Observation  (interleaved)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The agent emits explicit Thought: / Action: / Observation: traces.
This makes reasoning fully transparent and auditable.

Trajectory format:
  Thought:     "I need to find the current Bitcoin price first."
  Action:      web_search("Bitcoin price today")
  Observation: "BTC is $97,432 as of 2 minutes ago"
  Thought:     "Now I can calculate 15% of 97432..."
  Action:      calculator("97432 * 0.15")
  Observation: "14614.8"
  Action:      FINISH("15% of Bitcoin's price is $14,614.80")
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import anthropic

from config import settings
from memory.store import AgentMemory
from tools.base import ToolRegistry, ToolResult

logger = logging.getLogger("ReActAgent")


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class TrajectoryStep:
    iteration: int
    thought: str = ""
    action_tool: str = ""
    action_input: dict = field(default_factory=dict)
    observation: str = ""
    is_final: bool = False
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReActResult:
    success: bool
    answer: str
    iterations: int
    trajectory: list[TrajectoryStep]
    tool_calls: int
    elapsed_s: float
    error: str = ""

    def print_trajectory(self) -> None:
        """Pretty-print the full reasoning trace."""
        print("\n" + "═" * 65)
        print("  📜  REACT TRAJECTORY")
        print("═" * 65)
        for step in self.trajectory:
            print(f"\n  ── Iteration {step.iteration} ──")
            if step.thought:
                print(f"  \033[93m[THOUGHT   ]\033[0m {step.thought[:200]}")
            if step.action_tool:
                if step.is_final:
                    print(f"  \033[92m[FINISH    ]\033[0m {step.answer[:200]}")
                else:
                    print(f"  \033[95m[ACTION    ]\033[0m {step.action_tool}({json.dumps(step.action_input)[:100]})")
                    print(f"  \033[96m[OBSERVATION]\033[0m {step.observation[:200]}")
        print("\n" + "═" * 65)


# ─── ReActAgent ───────────────────────────────────────────────────────────────

class ReActAgent:
    """
    ReAct agent: explicit Thought/Action/Observation trace per iteration.

    Usage:
        registry = ToolRegistry().register(CalculatorTool()).register(WebSearchTool())
        agent = ReActAgent(registry)
        result = agent.run("What is 15% of the current Bitcoin price?")
        result.print_trajectory()
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
        self.memory = memory or AgentMemory("react_agent")
        self.model = model or settings.model
        self.max_iter = max_iterations or settings.max_iterations
        self.verbose = verbose

    # ── Public ─────────────────────────────────────────────────────────────────

    def run(self, goal: str) -> ReActResult:
        """Execute the ReAct loop for the given goal."""
        t0 = time.time()
        trajectory: list[TrajectoryStep] = []
        tool_call_count = 0
        self.memory.working.clear()

        logger.info(f"[ReAct] Starting: {goal[:80]}")
        self._print_banner(goal)

        messages: list[dict] = [{"role": "user", "content": goal}]

        for iteration in range(1, self.max_iter + 1):
            step = TrajectoryStep(iteration=iteration)

            # ── THINK: get next thought + action from LLM ──────────────────
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
                return ReActResult(False, "", iteration, trajectory,
                                   tool_call_count, time.time() - t0, str(e))

            # Extract thought text
            step.thought = self._extract_text(response)
            if step.thought and self.verbose:
                print(f"\n  \033[93m[THOUGHT {iteration:02d}]\033[0m {step.thought[:220]}")

            # ── ACT: finished? ──────────────────────────────────────────────
            if response.stop_reason == "end_turn":
                step.is_final = True
                step.answer = step.thought or "(no text)"
                trajectory.append(step)

                self.memory.remember(
                    f"ReAct goal: {goal[:60]}",
                    f"success in {iteration} steps",
                )
                elapsed = time.time() - t0
                self._print_done(iteration, tool_call_count, elapsed)

                return ReActResult(True, step.answer, iteration, trajectory,
                                   tool_call_count, elapsed)

            # ── ACT: tool call ──────────────────────────────────────────────
            if response.stop_reason == "tool_use":
                tool_results_for_api = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    step.action_tool = block.name
                    step.action_input = block.input
                    tool_call_count += 1

                    if self.verbose:
                        print(f"  \033[95m[ACTION   {iteration:02d}]\033[0m "
                              f"{block.name}({json.dumps(block.input)[:130]})")

                    # ── OBSERVE ─────────────────────────────────────────────
                    result: ToolResult = self.registry.execute(block.name, **block.input)
                    step.observation = result.to_str()

                    if self.verbose:
                        status = "✓" if result.success else "✗"
                        print(f"  \033[96m[OBSERVE  {iteration:02d}]\033[0m "
                              f"[{status}] {step.observation[:220]}")

                    self.memory.log(
                        f"[iter {iteration}] {block.name} → {step.observation[:80]}"
                    )

                    tool_results_for_api.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": step.observation,
                    })

                trajectory.append(step)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results_for_api})

        return ReActResult(False, "Max iterations reached.", self.max_iter,
                           trajectory, tool_call_count, time.time() - t0,
                           "max_iterations_exceeded")

    # ── Private helpers ────────────────────────────────────────────────────────

    def _system_prompt(self) -> str:
        tools_desc = "\n".join(
            f"  • {s['name']}: {s['description']}"
            for s in self.registry.all_schemas()
        )
        past = self.memory.episodic.recall("agent task", n=3)
        past_str = "\n".join(f"  - {e['text'][:80]}" for e in past) or "  (none)"

        return f"""You are a ReAct agent. You reason and act in an explicit loop:

THOUGHT  → reason about what to do next
ACTION   → call a tool to gather info or execute something
OBSERVATION → you receive the result
... repeat until you can give a final answer.

Available tools:
{tools_desc}

Past experience (for guidance):
{past_str}

Instructions:
- Think out loud before every action.
- Use tools when you need external information or computation.
- When you have a complete, accurate answer, stop calling tools and respond directly.
- Do not repeat tool calls with identical inputs.
- Be precise; cite numbers and sources from observations."""

    @staticmethod
    def _extract_text(response) -> str:
        return " ".join(
            block.text for block in response.content if hasattr(block, "text")
        ).strip()

    def _print_banner(self, goal: str) -> None:
        if not self.verbose:
            return
        w = 65
        print("\n" + "═" * w)
        print(f"  ⚡  ReAct AGENT  —  Thought → Action → Observation")
        print("═" * w)
        print(f"  Goal : {goal[:w-10]}")
        print(f"  Model: {self.model}   Max-iter: {self.max_iter}")
        print("─" * w)

    def _print_done(self, iters: int, calls: int, elapsed: float) -> None:
        if not self.verbose:
            return
        print("\n" + "─" * 65)
        print(f"  ✅ Done  —  {iters} step(s)  |  {calls} tool call(s)  |  {elapsed:.1f}s")
        print("═" * 65 + "\n")
