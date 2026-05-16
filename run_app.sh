#!/bin/bash

cd "$(dirname "$0")"

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install/upgrade dependencies if needed
pip install -q -r requirements.txt

# Launch Streamlit app
streamlit run app.py \
  --server.headless true \
  --browser.gatherUsageStats false
