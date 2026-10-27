#!/usr/bin/env bash
set -e

# Change directory to script folder
cd "$(dirname "$0")"

echo "=========================================================="
echo "🔬 DeepSearch Tool Reverse-Engineering Platform"
echo "=========================================================="

# Select best python executable (python3.13 preferred over 3.14 on macOS)
if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_CMD="python3.13"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    echo "Python 3 is required but not installed."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment using $PYTHON_CMD..."
    $PYTHON_CMD -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "Launching Streamlit Application on http://localhost:8501..."
streamlit run app.py
