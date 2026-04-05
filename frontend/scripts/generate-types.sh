#!/usr/bin/env bash
# frontend/scripts/generate-types.sh
set -euo pipefail

API_URL="${BEANBAY_API_URL:-http://localhost:8000}"
OUT="$(dirname "$0")/../src/api/types.ts"
TMP="$(mktemp /tmp/openapi-XXXXXX.json)"

trap 'rm -f "$TMP"' EXIT

echo "Fetching OpenAPI spec from ${API_URL}/openapi.json..."
curl -sf "${API_URL}/openapi.json" -o "$TMP"
bunx openapi-typescript "$TMP" -o "$OUT"
echo "Types written to ${OUT}"
