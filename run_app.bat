@echo off
title Ashish's Online Banking & Shopping System

echo.
echo ==================================================
echo    Ashish's Online Banking & Shopping System
echo ==================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please run install_dependencies.bat first
    pause
    exit /b 1
)

REM Start the application
echo Starting application...
echo.
python shopping_cart_and_banking-system.py

REM If the script gets here, the application has closed
echo.
echo Application closed.
pause
