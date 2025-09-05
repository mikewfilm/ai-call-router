#!/bin/bash

echo "🚀 Starting Integrated AI Call Router System..."
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down integrated system..."
    pkill -f "python.*app.py"
    pkill -f "python.*dashboard_simple.py"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "📥 Installing requirements..."
pip install Flask==2.3.3 Flask-Login==0.6.3 Werkzeug==2.3.7 requests

# Create data directory if it doesn't exist
mkdir -p data

echo ""
echo "🌐 Starting Voice App (Port 5003)..."
python app.py &
VOICE_PID=$!

echo "⏳ Waiting for voice app to start..."
sleep 3

echo ""
echo "📊 Starting Dashboard (Port 5004)..."
python dashboard_simple.py &
DASHBOARD_PID=$!

echo "⏳ Waiting for dashboard to start..."
sleep 3

echo ""
echo "✅ Integrated System Started Successfully!"
echo ""
echo "🌐 Voice App: http://localhost:5003"
echo "📊 Dashboard: http://localhost:5004"
echo "🔑 Dashboard Login: admin / admin123"
echo ""
echo "📋 Available Features:"
echo "   • Update store info in dashboard → affects voice app greeting"
echo "   • Add departments in dashboard → affects voice app routing"
echo "   • Add inventory in dashboard → affects voice app responses"
echo "   • Add coupons in dashboard → affects voice app promotions"
echo ""
echo "🧪 Test the integration:"
echo "   python test_integration.py"
echo ""
echo "📞 Test a call:"
echo "   curl -X POST http://localhost:5003/voice"
echo ""
echo "Press Ctrl+C to stop both systems"

# Wait for background processes
wait $VOICE_PID $DASHBOARD_PID
