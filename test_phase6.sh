#!/bin/bash
BASE_URL="http://127.0.0.1:5000"

echo "=========================================="
echo "STEP -1: Clean stale test transactions"
echo "=========================================="
python -c "
import sqlite3
conn = sqlite3.connect('instance/shop.db')
cur = conn.cursor()
cur.execute(\"DELETE FROM sync_queue WHERE id LIKE 'ffffffff-%' OR id LIKE 'cccccccc-%' OR id LIKE 'dddddddd-%' OR id LIKE 'eeeeeeee-%'\")
print('Deleted', cur.rowcount, 'stale test rows')
conn.commit()
conn.close()
"

echo ""
echo "=========================================="
echo "STEP 0: Baseline row counts"
echo "=========================================="
python -c "
import sqlite3
conn = sqlite3.connect('instance/shop.db')
cur = conn.cursor()
for t in ['sales', 'sync_queue', 'audit_logs']:
    cur.execute(f'SELECT COUNT(*) FROM {t}')
    print(f'{t}:', cur.fetchone()[0])
conn.close()
"

echo ""
echo "=========================================="
echo "STEP 1: Login as admin (john), manager (doe), employee (jane)"
echo "=========================================="
ADMIN_DEVICE="test-device-admin-001"
MANAGER_DEVICE="test-device-manager-001"
EMPLOYEE_DEVICE="test-device-employee-001"

ADMIN_LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d "{\"username\": \"john\", \"password\": \"1234567890\", \"device_id\": \"$ADMIN_DEVICE\"}")
MANAGER_LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d "{\"username\": \"doe\", \"password\": \"1234567890\", \"device_id\": \"$MANAGER_DEVICE\"}")
EMPLOYEE_LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d "{\"username\": \"jane\", \"password\": \"1234567890\", \"device_id\": \"$EMPLOYEE_DEVICE\"}")

ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | python -c "import sys,json; print(json.load(sys.stdin).get('token',''))")
MANAGER_TOKEN=$(echo "$MANAGER_LOGIN" | python -c "import sys,json; print(json.load(sys.stdin).get('token',''))")
EMPLOYEE_TOKEN=$(echo "$EMPLOYEE_LOGIN" | python -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

echo "Admin token: ${ADMIN_TOKEN:0:20}..."
echo "Manager token: ${MANAGER_TOKEN:0:20}..."
echo "Employee token: ${EMPLOYEE_TOKEN:0:20}..."

echo ""
echo "=========================================="
echo "STEP 2: Get a real product"
echo "=========================================="
PRODUCTS=$(curl -s "$BASE_URL/sales/products" -H "Authorization: Bearer $ADMIN_TOKEN")
PRODUCT_ID=$(echo "$PRODUCTS" | python -c "
import sys, json
d = json.load(sys.stdin)
items = d.get('items', [])
print(items[0]['id'] if items else '')
")
STOCK=$(echo "$PRODUCTS" | python -c "
import sys, json
d = json.load(sys.stdin)
items = d.get('items', [])
print(items[0]['stock_quantity'] if items else '')
")
echo "PRODUCT_ID: $PRODUCT_ID | STOCK: $STOCK"

echo ""
echo "=========================================="
echo "TEST 1: 3 valid new transactions — expect all 'synced'"
echo "=========================================="
TXN1="ffffffff-1111-1111-1111-111111111111"
TXN2="ffffffff-2222-2222-2222-222222222222"
TXN3="ffffffff-3333-3333-3333-333333333333"

curl -s -X POST "$BASE_URL/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"device_id\": \"$ADMIN_DEVICE\", \"transactions\": [
    {\"transaction_id\": \"$TXN1\", \"entity_type\": \"sale\", \"operation\": \"CREATE\", \"payload\": {\"items\": [{\"product_id\": \"$PRODUCT_ID\", \"quantity\": 1}], \"payment_method\": \"cash\"}, \"created_at\": \"2026-07-05T13:00:00Z\"},
    {\"transaction_id\": \"$TXN2\", \"entity_type\": \"sale\", \"operation\": \"CREATE\", \"payload\": {\"items\": [{\"product_id\": \"$PRODUCT_ID\", \"quantity\": 1}], \"payment_method\": \"cash\"}, \"created_at\": \"2026-07-05T13:01:00Z\"},
    {\"transaction_id\": \"$TXN3\", \"entity_type\": \"sale\", \"operation\": \"CREATE\", \"payload\": {\"items\": [{\"product_id\": \"$PRODUCT_ID\", \"quantity\": 1}], \"payment_method\": \"cash\"}, \"created_at\": \"2026-07-05T13:02:00Z\"}
  ]}"
echo ""

echo ""
echo "=========================================="
echo "TEST 2: Resend TXN1 (duplicate) — expect 'synced', no new sales row"
echo "=========================================="
python -c "
import sqlite3
c = sqlite3.connect('instance/shop.db').cursor()
c.execute('SELECT COUNT(*) FROM sales'); print('BEFORE:', c.fetchone()[0])
"
curl -s -X POST "$BASE_URL/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"device_id\": \"$ADMIN_DEVICE\", \"transactions\": [
    {\"transaction_id\": \"$TXN1\", \"entity_type\": \"sale\", \"operation\": \"CREATE\", \"payload\": {\"items\": [{\"product_id\": \"$PRODUCT_ID\", \"quantity\": 1}], \"payment_method\": \"cash\"}, \"created_at\": \"2026-07-05T13:00:00Z\"}
  ]}"
echo ""
python -c "
import sqlite3
c = sqlite3.connect('instance/shop.db').cursor()
c.execute('SELECT COUNT(*) FROM sales'); print('AFTER (should match):', c.fetchone()[0])
"

echo ""
echo "=========================================="
echo "TEST 3: Real stock conflict — qty $STOCK + 999999 (expect 'conflict')"
echo "=========================================="
TXN_CONFLICT="ffffffff-4444-4444-4444-444444444444"
curl -s -X POST "$BASE_URL/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"device_id\": \"$ADMIN_DEVICE\", \"transactions\": [
    {\"transaction_id\": \"$TXN_CONFLICT\", \"entity_type\": \"sale\", \"operation\": \"CREATE\", \"payload\": {\"items\": [{\"product_id\": \"$PRODUCT_ID\", \"quantity\": 999999}], \"payment_method\": \"cash\"}, \"created_at\": \"2026-07-05T13:05:00Z\"}
  ]}"
echo ""

echo ""
echo "=========================================="
echo "TEST 4: Nonexistent product — expect 'conflict'"
echo "=========================================="
TXN_DELETED="cccccccc-2222-2222-2222-222222222222"
curl -s -X POST "$BASE_URL/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"device_id\": \"$ADMIN_DEVICE\", \"transactions\": [
    {\"transaction_id\": \"$TXN_DELETED\", \"entity_type\": \"sale\", \"operation\": \"CREATE\", \"payload\": {\"items\": [{\"product_id\": \"nonexistent-product-id-0000\", \"quantity\": 1}], \"payment_method\": \"cash\"}, \"created_at\": \"2026-07-05T13:06:00Z\"}
  ]}"
echo ""

echo ""
echo "=========================================="
echo "TEST 5: device_id mismatch — expect 403"
echo "=========================================="
TXN_MISMATCH="dddddddd-2222-2222-2222-222222222222"
curl -s -w "\nHTTP_STATUS: %{http_code}\n" -X POST "$BASE_URL/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"device_id\": \"WRONG-DEVICE-ID-1234\", \"transactions\": [
    {\"transaction_id\": \"$TXN_MISMATCH\", \"entity_type\": \"sale\", \"operation\": \"CREATE\", \"payload\": {\"items\": [{\"product_id\": \"$PRODUCT_ID\", \"quantity\": 1}], \"payment_method\": \"cash\"}, \"created_at\": \"2026-07-05T13:07:00Z\"}
  ]}"
echo ""

echo ""
echo "=========================================="
echo "TEST 6: Batch size > 20 — expect 400"
echo "=========================================="
BIG_BATCH="["
for i in $(seq 1 21); do
  BIG_BATCH+="{\"transaction_id\": \"eeeeeeee-0000-0000-0000-$(printf '%012d' $i)\", \"entity_type\": \"sale\", \"operation\": \"CREATE\", \"payload\": {\"items\": [{\"product_id\": \"$PRODUCT_ID\", \"quantity\": 1}], \"payment_method\": \"cash\"}, \"created_at\": \"2026-07-05T13:08:00Z\"}"
  if [ $i -lt 21 ]; then BIG_BATCH+=","; fi
done
BIG_BATCH+="]"

curl -s -w "\nHTTP_STATUS: %{http_code}\n" -X POST "$BASE_URL/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"device_id\": \"$ADMIN_DEVICE\", \"transactions\": $BIG_BATCH}"
echo ""

echo ""
echo "=========================================="
echo "TEST 7: GET /sync/pull — expect products, users, deleted_product_ids, server_timestamp"
echo "=========================================="
curl -s "$BASE_URL/sync/pull" -H "Authorization: Bearer $ADMIN_TOKEN"
echo ""

echo ""
echo "=========================================="
echo "TEST 8: Admin approves the stock conflict (re-validates, still insufficient — expect still 'conflict')"
echo "=========================================="
curl -s -X POST "$BASE_URL/sync/resolve" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"transaction_id\": \"$TXN_CONFLICT\", \"resolution\": \"approve\"}"
echo ""

echo ""
echo "=========================================="
echo "TEST 9: Reject the deleted-product conflict — expect marks failed"
echo "=========================================="
curl -s -X POST "$BASE_URL/sync/resolve" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"transaction_id\": \"$TXN_DELETED\", \"resolution\": \"reject\"}"
echo ""

echo ""
echo "=========================================="
echo "TEST 10: Employee (jane) attempts /sync/resolve — expect 403"
echo "=========================================="
curl -s -w "\nHTTP_STATUS: %{http_code}\n" -X POST "$BASE_URL/sync/resolve" \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN" -H "Content-Type: application/json" \
  -d "{\"transaction_id\": \"$TXN_CONFLICT\", \"resolution\": \"approve\"}"
echo ""

echo ""
echo "=========================================="
echo "TEST 11: Manager (doe) approves a REAL fixable stock conflict — expect commits to 'synced'"
echo "=========================================="
TXN_CONFLICT2="ffffffff-5555-5555-5555-555555555555"

echo "Step A: force stock to 0 so the sale conflicts"
python -c "
import sqlite3
conn = sqlite3.connect('instance/shop.db')
cur = conn.cursor()
cur.execute(\"SELECT stock_quantity FROM products WHERE id = '$PRODUCT_ID'\")
original_stock = cur.fetchone()[0]
print('Original stock:', original_stock)
cur.execute(\"UPDATE products SET stock_quantity = 0 WHERE id = '$PRODUCT_ID'\")
conn.commit()
conn.close()
"

echo ""
echo "Step B: submit a sale for qty 1 — should now be a stock conflict"
curl -s -X POST "$BASE_URL/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"device_id\": \"$ADMIN_DEVICE\", \"transactions\": [
    {\"transaction_id\": \"$TXN_CONFLICT2\", \"entity_type\": \"sale\", \"operation\": \"CREATE\", \"payload\": {\"items\": [{\"product_id\": \"$PRODUCT_ID\", \"quantity\": 1}], \"payment_method\": \"cash\"}, \"created_at\": \"2026-07-05T13:06:00Z\"}
  ]}"
echo ""

echo ""
echo "Step C: restock the product — manager decides it's now fine to approve"
python -c "
import sqlite3
conn = sqlite3.connect('instance/shop.db')
cur = conn.cursor()
cur.execute(\"UPDATE products SET stock_quantity = 100 WHERE id = '$PRODUCT_ID'\")
conn.commit()
conn.close()
print('Stock restored to 100')
"

echo ""
echo "Step D: manager approves — should now be 'synced' with a server_id"
python -c "
import sqlite3
c = sqlite3.connect('instance/shop.db').cursor()
c.execute('SELECT COUNT(*) FROM sales'); print('sales BEFORE approve:', c.fetchone()[0])
"
curl -s -w "\nHTTP_STATUS: %{http_code}\n" -X POST "$BASE_URL/sync/resolve" \
  -H "Authorization: Bearer $MANAGER_TOKEN" -H "Content-Type: application/json" \
  -d "{\"transaction_id\": \"$TXN_CONFLICT2\", \"resolution\": \"approve\"}"
echo ""
python -c "
import sqlite3
c = sqlite3.connect('instance/shop.db').cursor()
c.execute('SELECT COUNT(*) FROM sales'); print('sales AFTER approve (should be +1):', c.fetchone()[0])
"

echo ""
echo "Step E: restore original stock so the DB isn't left corrupted for future tests"
python -c "
import sqlite3
conn = sqlite3.connect('instance/shop.db')
cur = conn.cursor()
cur.execute(\"UPDATE products SET stock_quantity = $STOCK WHERE id = '$PRODUCT_ID'\")
conn.commit()
conn.close()
print('Stock restored to original: $STOCK')
"

echo ""
echo "=========================================="
echo "FINAL row counts"
echo "=========================================="
python -c "
import sqlite3
conn = sqlite3.connect('instance/shop.db')
cur = conn.cursor()
for t in ['sales', 'sync_queue', 'audit_logs']:
    cur.execute(f'SELECT COUNT(*) FROM {t}')
    print(f'{t}:', cur.fetchone()[0])
"

echo ""
echo "=========================================="
echo "ALL TESTS COMPLETE"
echo "=========================================="