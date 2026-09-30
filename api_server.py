"""
api_server.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FastAPI REST wrapper for both Agent Loop and ReAct Agent.

Endpoints:
  POST /agent-loop/run   — runs the Perceive→Think→Act→Observe agent
  POST /react/run        — runs the Thought→Action→Observation agent
  GET  /health           — liveness check
  GET  /docs             — Swagger UI (auto-generated)

Start:
  pip install fastapi uvicorn
  python api_server.py
  # or: uvicorn api_server:app --reload --port 8000

Docker:
  docker compose up api
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("\n❌  FastAPI not installed.")
    print("    Run: pip install fastapi uvicorn\n")
    sys.exit(1)

from agents import AgentLoop, ReActAgent
from memory.store import AgentMemory
from tools import (
    ToolRegistry, CalculatorTool, FileReadTool,
    FileWriteTool, WebSearchTool, RunPythonTool, ListFilesTool,
)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Agentic AI API",
    description="REST interface for Agent Loop and ReAct Agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Shared registry ────────────────────────────────────────────────────────────
def make_registry() -> ToolRegistry:
    return (
        ToolRegistry()
        .register(CalculatorTool())
        .register(FileReadTool())
        .register(FileWriteTool())
        .register(WebSearchTool())
        .register(RunPythonTool())
        .register(ListFilesTool())
    )


# ── Request / Response models ──────────────────────────────────────────────────
class RunRequest(BaseModel):
    task: str
    max_iterations: int = 15
    verbose: bool = False


class RunResponse(BaseModel):
    success: bool
    answer: str
    iterations: int
    tool_calls: int
    elapsed_s: float
    error: str = ""


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "agents": ["agent-loop", "react"]}


@app.post("/agent-loop/run", response_model=RunResponse)
def run_agent_loop(req: RunRequest):
    """Run the Perceive→Think→Act→Observe agent."""
    try:
        agent = AgentLoop(
            tool_registry=make_registry(),
            memory=AgentMemory("loop_api"),
            max_iterations=req.max_iterations,
            verbose=req.verbose,
        )
        result = agent.run(req.task)
        return RunResponse(
            success=result.success,
            answer=result.answer,
            iterations=result.iterations,
            tool_calls=result.tool_calls,
            elapsed_s=result.elapsed_s,
            error=result.error,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/react/run", response_model=RunResponse)
def run_react(req: RunRequest):
    """Run the Thought→Action→Observation ReAct agent."""
    try:
        agent = ReActAgent(
            tool_registry=make_registry(),
            memory=AgentMemory("react_api"),
            max_iterations=req.max_iterations,
            verbose=req.verbose,
        )
        result = agent.run(req.task)
        return RunResponse(
            success=result.success,
            answer=result.answer,
            iterations=result.iterations,
            tool_calls=result.tool_calls,
            elapsed_s=result.elapsed_s,
            error=result.error,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Run directly ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
