"""
run_agent_loop.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 AGENT LOOP DEMO  —  Perceive → Think → Act → Observe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run from VS Code:
  • F5 → select "Agent Loop"
  • Or Terminal: python run_agent_loop.py
  • Custom task: python run_agent_loop.py --task "Your task here"
"""
import argparse
import sys
import json
from pathlib import Path

# ── Make sure local packages resolve ──────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from agents import AgentLoop
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


# ─── Build the shared tool registry ──────────────────────────────────────────

def build_registry() -> ToolRegistry:
    return (
        ToolRegistry()
        .register(CalculatorTool())
        .register(FileReadTool())
        .register(FileWriteTool())
        .register(WebSearchTool())          # needs TAVILY_API_KEY (graceful fallback)
        .register(RunPythonTool())
        .register(ListFilesTool())
    )


# ─── Demo tasks ───────────────────────────────────────────────────────────────

DEMO_TASKS = [
    # Task 0 — math + file write
    (
        "Calculate the compound interest on ₹50,000 at 8% per year for 3 years "
        "(compounded annually), then save the full working and result to "
        "'workspace/compound_interest.txt'."
    ),
    # Task 1 — code execution
    (
        "Write Python code that generates the first 10 Fibonacci numbers, "
        "run it, and save both the code and output to 'workspace/fibonacci.txt'."
    ),
    # Task 2 — file operations
    (
        "List the files in the current directory, then create a summary report "
        "at 'workspace/dir_report.txt' describing what you found."
    ),
]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agent Loop Demo")
    parser.add_argument("--task", type=str, default="", help="Custom task string")
    parser.add_argument("--demo", type=int, default=0, choices=[0, 1, 2],
                        help="Which built-in demo task to run (0/1/2)")
    parser.add_argument("--no-verbose", action="store_true", help="Suppress trace output")
    args = parser.parse_args()

    # Choose task
    task = args.task if args.task else DEMO_TASKS[args.demo]

    # Build components
    registry = build_registry()
    memory   = AgentMemory("loop_agent")
    agent    = AgentLoop(
        tool_registry=registry,
        memory=memory,
        verbose=not args.no_verbose,
    )

    # Run
    result = agent.run(task)

    # Output
    print("\n" + "━" * 65)
    print("  FINAL ANSWER")
    print("━" * 65)
    print(result.answer)
    print("\n  STATS:")
    print(f"    Success      : {result.success}")
    print(f"    Iterations   : {result.iterations}")
    print(f"    Tool calls   : {result.tool_calls}")
    print(f"    Elapsed      : {result.elapsed_s:.1f}s")

    # Save trajectory
    Path("logs").mkdir(exist_ok=True)
    traj_path = Path("logs/agent_loop_trajectory.json")
    traj_data = [
        {"iteration": s.iteration, "phase": s.phase,
         "content": str(s.content)[:300], "ts": s.ts}
        for s in result.steps
    ]
    traj_path.write_text(json.dumps(traj_data, indent=2))
    print(f"\n  Trajectory saved → {traj_path}")


if __name__ == "__main__":
    Path("workspace").mkdir(exist_ok=True)
    main()
