@echo off
chcp 65001 >nul
title Creation Automatique du Depot GitHub HERCULE
echo ======================================================================
echo    🏛️  CREATION & PUBLICATION AUTOMATIQUE SUR GITHUB : HERCULE  🏛️
echo ======================================================================
echo.

cd /d "%~dp0"
set "PATH=%PATH%;C:\Program Files\GitHub CLI"

echo [1/3] Verification de la connexion GitHub...
gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔐 Une fenetre de navigateur va s'ouvrir pour autoriser votre compte GitHub...
    gh auth login --hostname github.com --git-protocol https --web
)

echo.
echo [2/3] Creation du depot "HERCULE" sur votre compte GitHub et envoi du code...
gh repo create HERCULE --public --source=. --remote=origin --push --description "HERCULE v3.0 - Agent Personnel Autonome Multi-Agents (100%% Local)"

if %errorlevel% neq 0 (
    echo 🔄 Le depot existe peut-etre deja, envoi direct sur main...
    git push -u origin main
)

echo.
echo ✅ TERMINE ! Votre projet HERCULE est en ligne sur votre GitHub !
pause
