@echo off
chcp 65001 >nul
title HERCULE v3.0 - Interface Web Locale PHP (Port 8080)
echo ======================================================================
echo    🏛️  LANCEMENT DE L'INTERFACE WEB LOCALE PHP D'HERCULE (PORT 8080)
echo ======================================================================
echo.

cd /d "%~dp0"

set "PHP_BIN=php"
where php >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\xampp\php\php.exe" set "PHP_BIN=C:\xampp\php\php.exe"
    if exist "C:\laragon\bin\php\php.exe" set "PHP_BIN=C:\laragon\bin\php\php.exe"
)

echo 🌐 Ouverture de http://localhost:8080 dans votre navigateur...
start "" "http://localhost:8080"

echo 🚀 Serveur PHP local actif sur http://localhost:8080 (Ctrl+C pour arreter)
"%PHP_BIN%" -S localhost:8080 -t interface_php
pause
