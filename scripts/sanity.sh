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

echo
echo "7) Test speechModel=phone_call and numeric speechTimeout:"
if curl -s -X POST "$BASE/voice" | grep -q 'speechModel="phone_call"'; then
    echo "OK: speechModel=phone_call found"
else
    echo "FAIL: speechModel=phone_call not found"
fi

if curl -s -X POST "$BASE/voice" | grep -q 'speechTimeout="[0-9]'; then
    echo "OK: numeric speechTimeout found"
else
    echo "FAIL: numeric speechTimeout not found (should not be 'auto')"
fi

echo
echo "8) Test 404 error handler (should return 200 TwiML, not HTML):"
if curl -s -X POST "$BASE/does-not-exist" | grep -q '<Response>'; then
    echo "OK: 404 returns TwiML Response"
else
    echo "FAIL: 404 does not return TwiML Response"
fi

echo
echo "9) Test /result with missing job (should return 200 TwiML, not 404):"
if curl -s -X POST "$BASE/result?job=missing" | grep -q '<Response>'; then
    echo "OK: /result with missing job returns TwiML Response"
else
    echo "FAIL: /result with missing job does not return TwiML Response"
fi

echo
echo "10) Test Content-Type headers:"
CT=$(curl -s -I -X POST "$BASE/voice" | grep -i "content-type" | head -1)
if echo "$CT" | grep -q "text/xml"; then
    echo "OK: Content-Type is text/xml"
else
    echo "FAIL: Content-Type is not text/xml: $CT"
fi
