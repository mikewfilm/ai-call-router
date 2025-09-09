#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-https://ai-call-router-production.up.railway.app}"

echo "1) Minimal DIAG flow TwiML:"
curl -s -X POST "$BASE/diag/voice" | xmllint --format - | sed -n '1,120p'

echo
echo "2) Main flow TwiML:"
curl -s -X POST "$BASE/voice" | xmllint --format - | sed -n '1,120p'

echo
echo "3) DIAG handle echo (no body, should say no speech/digits):"
curl -s -X POST "$BASE/diag/handle" | xmllint --format - | sed -n '1,120p'

echo
echo "4) Main handle_gather (no body -> reprompt):"
curl -s -X POST "$BASE/handle_gather" | xmllint --format - | sed -n '1,160p'

echo
echo "5) Main handle_gather with SpeechResult:"
curl -s -X POST "$BASE/handle_gather" -d SpeechResult="two pounds of bananas" | xmllint --format - | sed -n '1,160p'

echo
echo "6) Scheme/host check (no http:// expected):"
curl -s -X POST "$BASE/voice" | grep -i "http://" && echo "Found http:// (fix needed)" || echo "OK: no http://"
