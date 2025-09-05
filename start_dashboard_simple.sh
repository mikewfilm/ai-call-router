#!/bin/bash

echo "🚀 Starting Store Management Dashboard (Simple Version)..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install basic requirements
echo "📥 Installing basic requirements..."
pip install Flask==2.3.3 Flask-Login==0.6.3 Werkzeug==2.3.7

# Start dashboard
echo "🗄️  Starting dashboard..."
python dashboard_simple.py

echo ""
echo "✅ Dashboard started successfully!"
echo "🌐 Access the dashboard at: http://localhost:5004"
echo "🔑 Default login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop the dashboard"
