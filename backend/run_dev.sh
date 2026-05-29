#!/bin/bash

# AI-PECO Backend Startup Script for macOS/Linux

echo ""
echo "==============================================="
echo "   AI-PECO Backend Startup"
echo "==============================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo ""
    echo "Please create .env file from .env.example:"
    echo "  cp .env.example .env"
    echo ""
    echo "Then edit .env and fill in:"
    echo "  - MONGODB_URL (from MongoDB Atlas)"
    echo "  - SECRET_KEY (generate: python -c \"import secrets; print(secrets.token_urlsafe(32))\")"
    echo ""
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

# Test imports
echo ""
echo "Testing imports..."
python test_imports.py
if [ $? -ne 0 ]; then
    echo "ERROR: Import test failed"
    exit 1
fi

echo ""
echo "✅ All checks passed!"
echo ""
echo "Starting FastAPI server..."
echo "Server will be available at: http://localhost:8000"
echo "API docs (Swagger): http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
