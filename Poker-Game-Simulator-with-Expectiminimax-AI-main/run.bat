@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo === Poker AI Simulator Setup (Windows) ===
echo Setting up Poker AI environment...

REM 1. Detect Python
where python >nul 2>nul
IF ERRORLEVEL 1 (
    echo Error: Python 3.10+ is not installed or not on PATH.
    echo Please install Python 3.10 or newer from https://www.python.org/downloads/windows/ and try again.
    goto :EOF
)

set PYTHON_BIN=python
echo Using Python interpreter: %PYTHON_BIN%

REM Move to project root (directory of this script)
cd /d %~dp0

REM 2. Create virtual environment if needed
IF NOT EXIST ".venv" (
    echo Creating virtual environment '.venv'...
    %PYTHON_BIN% -m venv .venv
) ELSE (
    echo Virtual environment '.venv' already exists. Reusing it.
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
IF EXIST "requirements.txt" (
    echo Found requirements.txt, installing listed packages (this may take a moment)...
    pip install -r requirements.txt
    IF ERRORLEVEL 1 (
        echo Dependency installation from requirements.txt failed once, retrying after upgrading pip...
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    )
) ELSE (
    echo No requirements.txt found. Installing base dependencies...
    pip install streamlit numpy pandas matplotlib
)

echo Verifying Streamlit installation...
python -c "import streamlit" >nul 2>nul
IF ERRORLEVEL 1 (
    echo Streamlit not found in environment. Installing...
    pip install streamlit
)

echo Launching Poker AI Simulator...
echo The Streamlit UI should open in your browser shortly.

where streamlit >nul 2>nul
IF ERRORLEVEL 1 (
    echo Error: Streamlit command not found even after installation.
    echo Try re-running this script, or manually run: python -m streamlit run main.py
    goto :EOF
)

streamlit run main.py

ENDLOCAL

