#!/usr/bin/env bash
# setup.sh ─── One-command local environment setup
# ─────────────────────────────────────────────────────────────────────────────
# Run: bash setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

BOLD="\033[1m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  🤖  Agentic AI Workspace — Local Setup${RESET}"
echo -e "${BOLD}════════════════════════════════════════════════════${RESET}"
echo ""

# ── 1. Python version check ────────────────────────────────────────────────────
echo -e "${BOLD}[1/5] Checking Python...${RESET}"
PYTHON=$(command -v python3 || command -v python || echo "")
if [ -z "$PYTHON" ]; then
  echo -e "${RED}❌ Python not found. Install Python 3.10+ from https://python.org${RESET}"
  exit 1
fi
PY_VER=$($PYTHON --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo -e "${GREEN}✓ Found $($PYTHON --version)${RESET}"

# ── 2. Create virtual environment ─────────────────────────────────────────────
echo ""
echo -e "${BOLD}[2/5] Creating virtual environment (.venv)...${RESET}"
if [ -d ".venv" ]; then
  echo -e "${YELLOW}  .venv already exists — skipping create${RESET}"
else
  $PYTHON -m venv .venv
  echo -e "${GREEN}✓ Created .venv${RESET}"
fi

# ── Activate venv ─────────────────────────────────────────────────────────────
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
  source .venv/Scripts/activate
else
  source .venv/bin/activate
fi
echo -e "${GREEN}✓ Virtual environment activated${RESET}"

# ── 3. Install dependencies ───────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[3/5] Installing dependencies...${RESET}"
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install fastapi uvicorn -q   # for api_server.py
echo -e "${GREEN}✓ Dependencies installed${RESET}"

# ── 4. Create .env from example ───────────────────────────────────────────────
echo ""
echo -e "${BOLD}[4/5] Configuring environment...${RESET}"
if [ -f ".env" ]; then
  echo -e "${YELLOW}  .env already exists — skipping${RESET}"
else
  cp .env.example .env
  echo -e "${GREEN}✓ Created .env from .env.example${RESET}"
  echo ""
  echo -e "${YELLOW}  ⚠  IMPORTANT: Open .env and add your ANTHROPIC_API_KEY${RESET}"
  echo -e "     Get your key at: ${BOLD}https://console.anthropic.com${RESET}"
fi

# ── 5. Create runtime directories ─────────────────────────────────────────────
echo ""
echo -e "${BOLD}[5/5] Creating runtime directories...${RESET}"
mkdir -p workspace logs memory/store
echo -e "${GREEN}✓ workspace/  logs/  memory/store/ created${RESET}"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  ✅ Setup complete!${RESET}"
echo -e "${BOLD}════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Next steps:"
echo ""
echo -e "  ${BOLD}1. Add your API key:${RESET}"
echo -e "     Open ${BOLD}.env${RESET} and set ANTHROPIC_API_KEY=sk-ant-..."
echo ""
echo -e "  ${BOLD}2. Run an agent:${RESET}"
echo -e "     ${GREEN}source .venv/bin/activate${RESET}          # activate venv"
echo -e "     ${GREEN}python run_agent_loop.py${RESET}           # Agent Loop"
echo -e "     ${GREEN}python run_react_agent.py${RESET}          # ReAct Agent"
echo ""
echo -e "  ${BOLD}3. Or open VS Code and press F5${RESET}"
echo ""
echo -e "  ${BOLD}4. Deploy with Docker:${RESET}"
echo -e "     ${GREEN}docker compose up --build${RESET}"
echo ""
