#!/bin/bash

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

source .venv/bin/activate

streamlit run app.py \
  --server.headless true \
  --browser.gatherUsageStats false
