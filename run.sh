#!/usr/bin/env bash
set -e

# Change directory to script folder
cd "$(dirname "$0")"

echo "=========================================================="
echo "🔬 DeepSearch Tool Reverse-Engineering Platform"
echo "=========================================================="

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment in .venv..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing / verifying dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "Launching Streamlit Application..."
streamlit run app.py
