@echo off
REM setup.bat ─── One-command Windows local setup
REM Run: setup.bat

echo.
echo ════════════════════════════════════════════════════
echo   Agentic AI Workspace — Windows Setup
echo ════════════════════════════════════════════════════
echo.

REM ── 1. Check Python ──────────────────────────────────────────────────────────
echo [1/5] Checking Python...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo  ERROR: Python not found.
    echo  Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo  OK: Python found

REM ── 2. Create virtual environment ────────────────────────────────────────────
echo.
echo [2/5] Creating virtual environment (.venv)...
IF EXIST ".venv" (
    echo  .venv already exists — skipping
) ELSE (
    python -m venv .venv
    echo  OK: Created .venv
)

REM ── 3. Activate and install ───────────────────────────────────────────────────
echo.
echo [3/5] Installing dependencies...
call .venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install fastapi uvicorn -q
echo  OK: Dependencies installed

REM ── 4. Create .env ────────────────────────────────────────────────────────────
echo.
echo [4/5] Configuring environment...
IF EXIST ".env" (
    echo  .env already exists — skipping
) ELSE (
    copy .env.example .env >nul
    echo  OK: Created .env
    echo.
    echo  IMPORTANT: Open .env and set ANTHROPIC_API_KEY
    echo  Get key at: https://console.anthropic.com
)

REM ── 5. Create directories ─────────────────────────────────────────────────────
echo.
echo [5/5] Creating runtime directories...
IF NOT EXIST "workspace" mkdir workspace
IF NOT EXIST "logs" mkdir logs
IF NOT EXIST "memory\store" mkdir memory\store
echo  OK: workspace\ logs\ memory\store\ created

REM ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo ════════════════════════════════════════════════════
echo   Setup complete!
echo ════════════════════════════════════════════════════
echo.
echo  Next steps:
echo.
echo  1. Edit .env  -  set ANTHROPIC_API_KEY=sk-ant-...
echo.
echo  2. Run an agent:
echo     .venv\Scripts\activate
echo     python run_agent_loop.py
echo     python run_react_agent.py
echo.
echo  3. Or open VS Code and press F5
echo.
echo  4. Deploy with Docker:
echo     docker compose up --build
echo.
pause
