@echo off
chcp 65001 >nul
title Creation Automatique du Depot GitHub : tremblaysnathan-maker/HERCULE
echo ======================================================================
echo    🏛️  CREATION & PUBLICATION SUR GITHUB : tremblaysnathan-maker/HERCULE
echo ======================================================================
echo.

cd /d "%~dp0"
set "PATH=%PATH%;C:\Program Files\GitHub CLI"

echo [1/3] Verification de la connexion GitHub (tremblaysnathan-maker)...
gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 🔐 Appuyez sur ENTREE pour ouvrir GitHub dans votre navigateur et valider le code :
    gh auth login --hostname github.com --git-protocol https --web
)

echo.
echo [2/3] Creation du depot "tremblaysnathan-maker/HERCULE" et envoi du code...
git remote remove origin >nul 2>&1
gh repo create tremblaysnathan-maker/HERCULE --public --source=. --remote=origin --push --description "HERCULE v3.0 - Agent Personnel Autonome Multi-Agents (100%% Local)"

if %errorlevel% neq 0 (
    echo 🔄 Envoi direct sur https://github.com/tremblaysnathan-maker/HERCULE.git ...
    git remote add origin https://github.com/tremblaysnathan-maker/HERCULE.git >nul 2>&1
    git push -u origin main
)

echo.
echo ======================================================================
echo ✅ TERMINE ! Votre depot est en ligne sur :
echo 👉 https://github.com/tremblaysnathan-maker/HERCULE
echo ======================================================================
pause
