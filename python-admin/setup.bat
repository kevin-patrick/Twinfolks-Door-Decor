@echo off
REM File: python-admin/setup.bat
REM Updated setup script for Twinfolks Wreath Manager with encoding detection

echo.
echo ========================================
echo   Twinfolks Wreath Manager Setup
echo ========================================
echo.

REM Check if Python 3.10 exists
if exist "C:\Users\kevin\AppData\Local\Programs\Python\Python310\python.exe" (
    echo [OK] Found Python 3.10
    set PYTHON_EXE=C:\Users\kevin\AppData\Local\Programs\Python\Python310\python.exe
) else (
    echo [ERROR] Python 3.10 not found at expected location
    echo Please install Python 3.10 from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing required packages...
echo.

REM Install packages
%PYTHON_EXE% -m pip install --upgrade pip
%PYTHON_EXE% -m pip install PySide6>=6.4.0
%PYTHON_EXE% -m pip install requests>=2.25.0
%PYTHON_EXE% -m pip install chardet>=5.0.0
%PYTHON_EXE% -m pip install PyInstaller>=5.0.0

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Setup complete!
    echo.
    echo You can now run:
    echo - run_app_pyside.bat (to start the application)
    echo - build_exe_pyside.bat (to create standalone .exe)
    echo.
) else (
    echo.
    echo [ERROR] Setup failed. Please check the error messages above.
    echo.
)

pause