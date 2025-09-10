#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-https://ai-call-router-production.up.railway.app}"
curl -sS "$BASE/healthz" || true
curl -sS -X POST "$BASE/voice" | xmllint --format - | sed -n '1,60p'
curl -sS -X POST "$BASE/handle_gather" -d SpeechResult="two pounds of bananas" | xmllint --format - | sed -n '1,60p'
