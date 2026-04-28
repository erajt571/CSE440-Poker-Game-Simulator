#!/usr/bin/env bash

set -e

echo "=== Poker AI Simulator Setup (macOS/Linux) ==="
echo "Setting up Poker AI environment..."

# 1. Detect Python
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Error: Python 3.10+ is not installed or not on PATH."
  echo "Please install Python 3.10 or newer from https://www.python.org/downloads/ and try again."
  exit 1
fi

echo "Using Python interpreter: ${PYTHON_BIN}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 2. Create virtual environment if needed
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment '.venv'..."
  "${PYTHON_BIN}" -m venv .venv
else
  echo "Virtual environment '.venv' already exists. Reusing it."
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
  echo "Found requirements.txt, installing listed packages (this may take a moment)..."
  if ! pip install -r requirements.txt; then
    echo "Dependency installation from requirements.txt failed once, retrying after upgrading pip..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
  fi
else
  echo "No requirements.txt found. Installing base dependencies..."
  pip install streamlit numpy pandas matplotlib
fi

echo "Verifying Streamlit installation..."
if ! python -c "import streamlit" >/dev/null 2>&1; then
  echo "Streamlit not found in environment. Installing..."
  pip install streamlit
fi

echo "Launching Poker AI Simulator..."
echo "The Streamlit UI should open in your browser shortly."

if ! command -v streamlit >/dev/null 2>&1; then
  echo "Error: Streamlit command not found even after installation."
  echo "Try re-running this script, or manually run: python -m streamlit run main.py"
  exit 1
fi

streamlit run main.py

