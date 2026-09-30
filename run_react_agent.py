"""
run_react_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ ReAct AGENT DEMO  —  Thought → Action → Observation (loop)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run from VS Code:
  • F5 → select "ReAct Agent"
  • Or Terminal: python run_react_agent.py
  • Custom task: python run_react_agent.py --task "Your question here"
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents import ReActAgent
from memory.store import AgentMemory
from tools import (
    ToolRegistry,
    CalculatorTool,
    FileReadTool,
    FileWriteTool,
    WebSearchTool,
    RunPythonTool,
    ListFilesTool,
)

DEMO_TASKS = [
    # 0 — multi-step math + research
    (
        "What is the compound interest on $10,000 invested at 7.5% annually "
        "for 5 years? Show all steps, then write a full report to "
        "'workspace/investment_report.txt'."
    ),
    # 1 — code generation + execution + save
    (
        "Write Python code to generate a multiplication table (1-10), "
        "execute it, verify the output is correct, then save the code "
        "and its output to 'workspace/multiplication_table.txt'."
    ),
    # 2 — filesystem analysis
    (
        "Explore the current directory, list all files, identify any Python "
        "files, read one of them, and produce a brief summary saved to "
        "'workspace/code_summary.txt'."
    ),
]


def build_registry() -> ToolRegistry:
    return (
        ToolRegistry()
        .register(CalculatorTool())
        .register(FileReadTool())
        .register(FileWriteTool())
        .register(WebSearchTool())
        .register(RunPythonTool())
        .register(ListFilesTool())
    )


def main():
    parser = argparse.ArgumentParser(description="ReAct Agent Demo")
    parser.add_argument("--task", type=str, default="",
                        help="Custom task for the agent")
    parser.add_argument("--demo", type=int, default=0, choices=[0, 1, 2],
                        help="Built-in demo task number")
    parser.add_argument("--no-verbose", action="store_true",
                        help="Hide step-by-step trace")
    parser.add_argument("--trajectory", action="store_true",
                        help="Print full trajectory at the end")
    args = parser.parse_args()

    task = args.task if args.task else DEMO_TASKS[args.demo]

    registry = build_registry()
    memory   = AgentMemory("react_agent")
    agent    = ReActAgent(
        tool_registry=registry,
        memory=memory,
        verbose=not args.no_verbose,
    )

    result = agent.run(task)

    # ── Print result ──────────────────────────────────────────────────
    print("\n" + "━" * 65)
    print("  FINAL ANSWER")
    print("━" * 65)
    print(result.answer)

    print("\n  STATS:")
    print(f"    Success    : {result.success}")
    print(f"    Steps      : {result.iterations}")
    print(f"    Tool calls : {result.tool_calls}")
    print(f"    Elapsed    : {result.elapsed_s:.1f}s")

    if args.trajectory:
        result.print_trajectory()

    # ── Save trajectory JSON ──────────────────────────────────────────
    Path("logs").mkdir(exist_ok=True)
    log_path = Path("logs/react_trajectory.json")
    log_data = [
        {
            "iteration": s.iteration,
            "thought":   s.thought[:300],
            "action":    s.action_tool,
            "input":     s.action_input,
            "observation": s.observation[:300],
            "is_final":  s.is_final,
        }
        for s in result.trajectory
    ]
    log_path.write_text(json.dumps(log_data, indent=2))
    print(f"\n  Trajectory saved → {log_path}")


if __name__ == "__main__":
    Path("workspace").mkdir(exist_ok=True)
    main()
