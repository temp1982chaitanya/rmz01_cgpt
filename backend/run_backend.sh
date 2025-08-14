#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if not installed
if ! python -c "import fastapi" >/dev/null 2>&1; then
    echo "📦 Installing backend dependencies..."
    pip install -r requirements.txt
fi

# Run the backend server
echo "🚀 Starting backend server..."
python mobile_card_detection.py > backend.log 2>&1 &
