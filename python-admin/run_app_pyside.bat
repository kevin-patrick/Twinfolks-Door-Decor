@echo off
REM File: python-admin/run_app_pyside.bat
REM Run script for Twinfolks Wreath Manager (PySide6 version)

echo.
echo ========================================
echo   Twinfolks Wreath Manager (PySide6)
echo ========================================
echo.

REM Check if Python 3.10 exists
if exist "C:\Users\kevin\AppData\Local\Programs\Python\Python310\python.exe" (
    echo 🐍 Using Python 3.10
    set PYTHON_EXE=C:\Users\kevin\AppData\Local\Programs\Python\Python310\python.exe
) else (
    echo ❌ Python 3.10 not found at expected location
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo 🚀 Starting Twinfolks Wreath Manager (PySide6)...
echo.

%PYTHON_EXE% main_pyside.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Application error occurred.
    echo.
    pause
)