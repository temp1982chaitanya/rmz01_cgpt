#!/bin/bash

# Navigate to the frontend directory
cd "$(dirname "$0")"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Node.js and npm
if ! command_exists node || ! command_exists npm; then
    echo "❌ Node.js and/or npm are not installed. Please install them to continue."
    exit 1
fi

# Install dependencies if node_modules directory doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies."
        exit 1
    fi
fi

# Start the frontend server
echo "🚀 Starting frontend development server..."
npm run dev
