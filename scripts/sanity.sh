#!/usr/bin/env bash
set -euo pipefail
BASE="${PUBLIC_BASE:-http://127.0.0.1:5000}"

echo "GET /healthz"; curl -sSf "$BASE/healthz" | jq .
echo "GET /whoami";  curl -sSf "$BASE/whoami"

# TwiML should be XML and https links
echo "POST /voice (should return TwiML with https)"
curl -sS -X POST "$BASE/voice" -d "Caller=+15551234567" -H "Content-Type: application/x-www-form-urlencoded" -D - | tee /tmp/voice.out
file -b --mime-type /tmp/voice.out | grep -qi "xml" || (echo "❌ not xml" && exit 1)
grep -q "https://" /tmp/voice.out || (echo "❌ TwiML missing https" && exit 1)
echo "✅ /voice TwiML looks good"