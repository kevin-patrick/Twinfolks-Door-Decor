@echo off
REM File: python-admin/build_exe_pyside.bat
REM Build standalone executable for Twinfolks Wreath Manager (PySide6)

echo.
echo ========================================
echo   Build Twinfolks Wreath Manager EXE
echo ========================================
echo.

set PYTHON_EXE=C:\Users\kevin\AppData\Local\Programs\Python\Python310\python.exe

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python 3.10 not found at expected location
    echo Expected: %PYTHON_EXE%
    pause
    exit /b 1
)

echo Using Python 3.10 for building...
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "main_pyside.spec" del "main_pyside.spec"

echo.
echo Building standalone executable...
echo This will take 5-10 minutes - please be patient!
echo.

REM Build the executable
"%PYTHON_EXE%" -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "TwinfolksWreathManager" ^
    --add-data "*.py;." ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtWidgets" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "requests" ^
    --hidden-import "json" ^
    --hidden-import "uuid" ^
    --clean ^
    main_pyside.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   BUILD SUCCESSFUL!
    echo ========================================
    echo.
    
    if exist "dist\TwinfolksWreathManager.exe" (
        echo EXE created: dist\TwinfolksWreathManager.exe
        
        REM Get file size
        for %%I in ("dist\TwinfolksWreathManager.exe") do set size=%%~zI
        set /a sizeMB=!size!/1024/1024
        echo File size: !sizeMB! MB
        
        echo.
        echo SUCCESS! Your standalone executable is ready.
        echo.
        echo Location: dist\TwinfolksWreathManager.exe
        echo.
        echo This .exe file can run on ANY Windows computer
        echo without needing Python installed!
        echo.
        echo You can copy just this .exe file to your wife's computer
        echo and it will work perfectly.
        echo.
        
    ) else (
        echo ERROR: Executable not found after build.
    )
    
) else (
    echo.
    echo BUILD FAILED!
    echo Check the error messages above.
    echo.
)

pause