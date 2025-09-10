#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-https://ai-call-router-production.up.railway.app}"

echo "== /result missing job should return TwiML =="
curl -s -X POST "$BASE/result?job=does-not-exist&n=1" | grep -qi "<Response>"

echo "== content-type must be text/xml =="
ct=$(curl -s -D - -o /dev/null -X POST "$BASE/result?job=does-not-exist&n=1" | tr -d '\r' | awk -F': ' '/^Content-Type/ {print $2}')
echo "$ct" | grep -qi "text/xml"

echo "OK"
