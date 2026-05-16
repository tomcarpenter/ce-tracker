#!/bin/bash

# Optional setup script for manual virtual environment initialization

cd "$(dirname "$0")"

echo "Creating Python virtual environment..."
python3 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete. Run: ./run_app.sh"
