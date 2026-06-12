#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
EMAIL="${E2E_EMAIL:-e2e-$(date +%s)@example.com}"
PASSWORD="${E2E_PASSWORD:-TestPass123!}"

echo "=== Banviro AI E2E ==="
echo "API: $API_URL"
echo "User: $EMAIL"
echo

echo "1. AI status"
curl -s "$API_URL/api/v1/ai/status" | python3 -m json.tool
echo

echo "2. Register + login"
curl -s -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"E2E User\"}" > /dev/null

TOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token acquired (${#TOKEN} chars)"
echo

echo "3. Create expense transaction"
CAT_ID=$(curl -s "$API_URL/api/v1/finance/categories?type=expense" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

TX=$(curl -s -X POST "$API_URL/api/v1/finance/transactions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"amount\":150.50,\"type\":\"expense\",\"category_id\":$CAT_ID,\"description\":\"Supermarket Lidl saptamana\",\"transaction_date\":\"2026-06-10\"}")

TX_ID=$(echo "$TX" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Created transaction id=$TX_ID"
sleep 2
echo

echo "4. Update transaction (reindex trigger)"
curl -s -X PUT "$API_URL/api/v1/finance/transactions/$TX_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"amount\":175.00,\"type\":\"expense\",\"category_id\":$CAT_ID,\"description\":\"Supermarket Lidl saptamana actualizat\",\"transaction_date\":\"2026-06-10\"}" \
  | python3 -c "import sys,json; t=json.load(sys.stdin); print(f\"Updated amount={t['amount']} desc={t['description']}\")"
sleep 2
echo

echo "5. Reindex"
curl -s -X POST "$API_URL/api/v1/ai/reindex" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo

echo "6. Chat finance (sync)"
curl -s --max-time 120 -X POST "$API_URL/api/v1/ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Cat am cheltuit luna asta si care e soldul?","locale":"ro"}' \
  | python3 -m json.tool
echo

echo "7. Chat RAG (sync)"
curl -s --max-time 120 -X POST "$API_URL/api/v1/ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Explica-mi tendinta cheltuielilor la supermarket","locale":"ro"}' \
  | python3 -m json.tool
echo

echo "8. Chat stream (first events)"
curl -s --max-time 120 -N -X POST "$API_URL/api/v1/ai/chat/stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Cum stau bugetele mele?","locale":"ro"}' \
  | head -n 20 || true

echo
echo "=== E2E complete ==="
