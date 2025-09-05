#!/bin/bash

echo "🔄 Stopping any existing Flask processes..."
pkill -f "python3 app.py" 2>/dev/null || true
pkill -f "flask" 2>/dev/null || true

echo "🧹 Waiting for processes to stop..."
sleep 2

echo "🔍 Checking if port 5003 is free..."
if lsof -i :5003 >/dev/null 2>&1; then
    echo "⚠️  Port 5003 is still in use. Force killing..."
    lsof -ti:5003 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

echo "🚀 Starting Flask app on port 5003..."
echo "📝 You can stop the app with Ctrl+C"
echo "🔗 Health check: http://localhost:5003/health"
echo ""

export CONSENT_FUNCTION_URL="https://consent-service-9381.twil.io/voice-consent"
export TWILIO_MESSAGING_SERVICE_SID="MGd54fcd89a0dc2d0de01e0f34e84bd265"
export TWILIO_FROM_NUMBER="+18555924387"
python3 app.py
