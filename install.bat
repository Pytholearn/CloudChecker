@echo off
title Cloud Checker - Installer
color 0E

echo.
echo   ================================================
echo            Cloud Checker - Installer
echo            github.com/Pytholearn
echo   ================================================
echo.

:: Check Python
echo   [1/3] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [ERROR] Python is not installed or not in PATH.
    echo   Download from: https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%V in ('python --version 2^>^&1') do echo   Found Python %%V

:: Install dependencies
echo.
echo   [2/3] Installing dependencies...
pip install rich --quiet
pip install autoupgrader --quiet

echo   Dependencies installed.

:: Verify
echo.
echo   [3/3] Verifying...
python -c "from rich.console import Console; print('   Rich: OK')"
python -c "import autoupgrader; print('   Autoupgrader: OK')"

echo.
echo   ================================================
echo            Installation Complete!
echo.
echo            Run:  python CloudChecker.py
echo   ================================================
echo.
pause
