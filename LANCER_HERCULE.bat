@echo off
chcp 65001 >nul
title HERCULE v3.0 - Agent Autonome Multi-Agents (100%% Local)
echo ======================================================================
echo    🏛️  DEMARRAGE DE L'AGENT HERCULE v3.0 (EXECUTION 100%% LOCALE)  🏛️
echo ======================================================================
echo.

cd /d "%~dp0"

if not exist ".venv" (
    echo [1/3] Creation de l'environnement virtuel Python local (.venv)...
    python -m venv .venv
)

echo [2/3] Verification des dependances locales...
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo [3/3] Lancement du coeur HERCULE sur http://localhost:8000 ...
python start.py
pause
