# 🤖 Agentic AI Workspace

Two production-ready AI agents you can run locally from VS Code — today.

```
Agent Loop  →  Perceive → Think → Act → Observe  (repeats)
ReAct       →  Thought  → Action → Observation   (interleaved trace)
```

---

## 📁 Project Structure

```
agentic_workspace/
│
├── agents/
│   ├── agent_loop.py       ← Perceive→Think→Act→Observe pattern
│   └── react_agent.py      ← Thought/Action/Observation pattern
│
├── tools/
│   ├── base.py             ← ToolBase, ToolRegistry, ToolResult
│   └── builtin.py          ← calculator, file_read/write, web_search,
│                              run_python, list_files
├── memory/
│   └── store.py            ← WorkingMemory + EpisodicMemory (ChromaDB)
│
├── config/
│   └── settings.py         ← Loads .env, centralises all config
│
├── run_agent_loop.py        ← ▶ Run Agent Loop from terminal or VS Code F5
├── run_react_agent.py       ← ▶ Run ReAct Agent from terminal or VS Code F5
├── api_server.py            ← FastAPI REST wrapper (optional)
│
├── Dockerfile               ← Container build
├── docker-compose.yml       ← Full local stack
│
├── setup.sh                 ← Mac/Linux one-command setup
├── setup.bat                ← Windows one-command setup
├── requirements.txt
├── .env.example             ← Copy → .env, add your API key
└── .vscode/
    ├── launch.json          ← F5 run configurations (7 presets)
    ├── settings.json        ← Python interpreter, formatter
    └── extensions.json      ← Recommended extensions
```

---

## ⚡ Quickstart (< 5 minutes)

### Step 1 — Clone / open in VS Code

```bash
# If you downloaded a zip:
cd agentic_workspace

# Open in VS Code
code .
```

### Step 2 — Run setup

**Mac / Linux:**
```bash
bash setup.sh
```

**Windows:**
```bat
setup.bat
```

This creates `.venv`, installs all packages, and copies `.env.example → .env`.

---

### Step 3 — Add your API key

Open `.env` (created by setup) and fill in:

```env
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

Get your key at → **https://console.anthropic.com**

Optionally add a Tavily key for real web search (free tier at tavily.com):
```env
TAVILY_API_KEY=tvly-YOUR_KEY_HERE
```

---

### Step 4 — Run an agent

**Option A: VS Code F5 (easiest)**
```
1. Open VS Code
2. Press F5
3. Select a configuration from the dropdown:
   • 🔄 Agent Loop (Demo 0 - Compound Interest)
   • ⚡ ReAct Agent (Demo 0 - Investment Report)
   • ... 7 presets total
4. Watch the terminal
```

**Option B: Terminal**
```bash
# Activate your virtual environment first
source .venv/bin/activate        # Mac/Linux
.venv\Scripts\activate           # Windows

# Run Agent Loop
python run_agent_loop.py

# Run ReAct Agent
python run_react_agent.py

# Run with full trajectory printed
python run_react_agent.py --trajectory

# Run a custom task
python run_agent_loop.py --task "Analyse the files in this directory and summarise them"
python run_react_agent.py --task "What is 15% of 84,000? Save result to workspace/calc.txt"

# Choose a built-in demo (0, 1, or 2)
python run_agent_loop.py --demo 1
python run_react_agent.py --demo 2
```

---

## 🔍 What Each Agent Does

### 🔄 Agent Loop — `run_agent_loop.py`

```
Each iteration:
  PERCEIVE  ─── gather goal + available tools + memory context
  THINK     ─── LLM decides: use a tool, or finish?
  ACT       ─── execute the chosen tool
  OBSERVE   ─── record result → feed back → next iteration
```

**Console output looks like:**
```
═══════════════════════════════════════════════════════════════════
  🔄  AGENT LOOP  —  Perceive → Think → Act → Observe
═══════════════════════════════════════════════════════════════════
  Goal : Calculate compound interest on ₹50,000...
  Model: claude-opus-4-6   Max-iter: 15
──────────────────────────────────────────────────────────────────
  [PERCEIVE] {'goal': '...', 'iteration': 1, 'tools_available': [...]}
  [THINK   ] I need to calculate A = P(1 + r/n)^nt...
  [ACT     ] Tool: calculator  Input: {"expression": "50000*(1+0.08)**3"}
  [OBSERVE ] ✓ {"expression": "50000*(1+0.08)**3", "result": 62985.6}
  [ACT     ] Tool: file_write  Input: {"path": "workspace/..."}
  [OBSERVE ] ✓ {"path": "workspace/compound_interest.txt", ...}
──────────────────────────────────────────────────────────────────
  ✅ Done  —  2 iteration(s)  |  2 tool call(s)  |  3.4s
```

---

### ⚡ ReAct Agent — `run_react_agent.py`

```
Each step:
  THOUGHT      ─── "I need to search for X because..."
  ACTION       ─── tool_name(arguments)
  OBSERVATION  ─── tool result
  THOUGHT      ─── "Now I know X, next I should..."
  ... repeat until FINISH
```

**Console output looks like:**
```
═══════════════════════════════════════════════════════════════════
  ⚡  ReAct AGENT  —  Thought → Action → Observation
═══════════════════════════════════════════════════════════════════

  [THOUGHT 01] I need to calculate compound interest on $10,000
               at 7.5% for 5 years. Formula: A = P(1+r)^n

  [ACTION   01] calculator({"expression": "10000*(1+0.075)**5"})
  [OBSERVE  01] ✓ {"result": 14356.29}

  [THOUGHT 02] Got the result: $14,356.29. Now I'll write the
               full report to the workspace file.

  [ACTION   02] file_write({"path": "workspace/investment_report.txt", ...})
  [OBSERVE  02] ✓ {"bytes_written": 412}

  ✅ Done  —  2 step(s)  |  2 tool call(s)  |  4.1s
```

---

## 🛠️ Built-in Tools

| Tool | What it does | Example input |
|------|-------------|---------------|
| `calculator` | Safe math eval | `"15000 * 0.08 ** 3"` |
| `file_read` | Read any local file | `path: "data/report.csv"` |
| `file_write` | Write/append files | `path: "out.txt", content: "..."` |
| `list_files` | List a directory | `path: "."` |
| `run_python` | Execute Python code | `code: "print([x**2 for x in range(5)])"` |
| `web_search` | Tavily web search | `query: "Python 3.12 release notes"` |

---

## ➕ Adding Your Own Tool

Create a new file `tools/my_tool.py`:

```python
from tools.base import ToolBase

class SendEmailTool(ToolBase):
    name = "send_email"
    description = "Send an email to a recipient"

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "to":      {"type": "string", "description": "Recipient email"},
                "subject": {"type": "string", "description": "Email subject"},
                "body":    {"type": "string", "description": "Email body"},
            },
            "required": ["to", "subject", "body"],
        }

    def _run(self, to: str, subject: str, body: str) -> dict:
        # Your logic here — e.g. smtplib or SendGrid
        print(f"📧 Sending to {to}: {subject}")
        return {"sent": True, "to": to}
```

Then register it in your runner:

```python
from tools.my_tool import SendEmailTool

registry = ToolRegistry().register(SendEmailTool()).register(CalculatorTool())
agent = ReActAgent(registry)
```

---

## 🚀 Deployment

### Option 1 — Docker (recommended)

```bash
# Build and run everything
docker compose up --build

# Run just the ReAct agent once
docker compose run react-agent

# Run Agent Loop with a custom task
docker compose run react-agent python run_react_agent.py \
  --task "Summarise all files in workspace/"

# Start the REST API
docker compose up api
# → http://localhost:8000
# → http://localhost:8000/docs   (Swagger UI)
```

### Option 2 — FastAPI REST API

```bash
pip install fastapi uvicorn
python api_server.py
# → http://localhost:8000
```

**Call the API:**
```bash
# ReAct agent via curl
curl -X POST http://localhost:8000/react/run \
  -H "Content-Type: application/json" \
  -d '{"task": "What is 20% of 85000? Save to workspace/result.txt"}'

# Agent Loop via curl
curl -X POST http://localhost:8000/agent-loop/run \
  -H "Content-Type: application/json" \
  -d '{"task": "List all .py files and count lines in each"}'

# Health check
curl http://localhost:8000/health
```

**Response:**
```json
{
  "success": true,
  "answer": "20% of 85,000 is 17,000. Saved to workspace/result.txt.",
  "iterations": 2,
  "tool_calls": 2,
  "elapsed_s": 3.8
}
```

### Option 3 — Cloud (AWS / GCP / Azure)

**AWS ECS (Fargate):**
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com

docker build -t agentic-ai .
docker tag agentic-ai:latest <ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/agentic-ai:latest
docker push <ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/agentic-ai:latest

# Create ECS task definition + service via AWS Console or CLI
# Set ANTHROPIC_API_KEY as a secret in AWS Secrets Manager
```

**GCP Cloud Run:**
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/agentic-ai
gcloud run deploy agentic-ai \
  --image gcr.io/YOUR_PROJECT/agentic-ai \
  --platform managed \
  --region us-central1 \
  --set-env-vars ANTHROPIC_API_KEY=sk-ant-...
```

---

## ⚙️ Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(required)* | From console.anthropic.com |
| `TAVILY_API_KEY` | *(optional)* | Web search. Graceful fallback if missing |
| `AGENT_MODEL` | `claude-opus-4-6` | Any Anthropic model |
| `AGENT_MAX_ITERATIONS` | `15` | Max loop iterations before stopping |
| `AGENT_LOG_LEVEL` | `INFO` | DEBUG / INFO / WARNING |

---

## 🐞 Troubleshooting

**`ANTHROPIC_API_KEY is not set`**
→ Open `.env`, make sure your key is there with no spaces

**`ModuleNotFoundError: No module named 'anthropic'`**
→ Run: `source .venv/bin/activate` then `pip install -r requirements.txt`

**`web_search returns mock result`**
→ Normal! Set `TAVILY_API_KEY` in `.env` for real results

**`chromadb` errors on import**
→ Run: `pip install chromadb sentence-transformers`
→ Memory still works via `WorkingMemory` even without ChromaDB

**Docker `env_file: .env` error**
→ Make sure `.env` exists: `cp .env.example .env`

---

## 📜 Logs & Outputs

```
logs/
  agent_loop_trajectory.json   ← Perceive/Think/Act/Observe per step
  react_trajectory.json        ← Thought/Action/Observation per step

workspace/
  compound_interest.txt        ← Files written by agents
  fibonacci.txt
  ...
```

---

## 🔗 Key Links

| Resource | URL |
|----------|-----|
| Anthropic Console (API key) | https://console.anthropic.com |
| Anthropic Docs | https://docs.anthropic.com |
| Tool Use Guide | https://docs.anthropic.com/en/docs/tool-use |
| Tavily (web search) | https://tavily.com |
| ChromaDB docs | https://docs.trychroma.com |
