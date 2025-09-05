#!/bin/bash

echo "🚀 Starting Store Management Dashboard..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "📥 Installing dashboard requirements..."
pip install -r requirements_dashboard.txt

# Initialize database and start dashboard
echo "🗄️  Initializing database..."
python dashboard.py

echo ""
echo "✅ Dashboard started successfully!"
echo "🌐 Access the dashboard at: http://localhost:5004"
echo "🔑 Default login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop the dashboard"
