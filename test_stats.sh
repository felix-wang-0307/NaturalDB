#!/bin/bash
# Test script for HomePage statistics

echo "========================================"
echo "Testing HomePage Statistics API"
echo "========================================"
echo ""

echo "1. Total Products:"
curl -s "http://localhost:8080/api/databases/demo_user/amazon/query/count" \
  -H "Content-Type: application/json" \
  -d '{"table": "Products"}' | jq '.count'

echo ""
echo "2. Highly Rated Products (≥4.5★):"
curl -s "http://localhost:8080/api/databases/demo_user/amazon/query/count" \
  -H "Content-Type: application/json" \
  -d '{"table": "Products", "filters": [{"field": "rating", "operator": "gte", "value": 4.5}]}' | jq '.count'

echo ""
echo "3. Big Discounts (≥60%):"
curl -s "http://localhost:8080/api/databases/demo_user/amazon/query/count" \
  -H "Content-Type: application/json" \
  -d '{"table": "Products", "filters": [{"field": "discount_percentage", "operator": "gte", "value": 60}]}' | jq '.count'

echo ""
echo "========================================"
echo "All statistics loaded successfully!"
echo "========================================"
