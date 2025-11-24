#!/usr/bin/env python3
"""
Test script for NaturalDB REST API

Run the API server first:
    python run_api.py

Then run this test script:
    python test_api.py
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:5000"

def print_response(response, title="Response"):
    """Pretty print response"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(response.text)
    print(f"{'='*60}\n")


def test_api():
    """Test API endpoints"""
    
    print(f"\n🚀 Testing NaturalDB REST API at {BASE_URL}\n")
    
    # Test 1: Health check
    print("1️⃣ Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check")
    
    # Test 2: Create user
    print("2️⃣ Creating user 'alice'...")
    response = requests.post(f"{BASE_URL}/api/users", json={
        "user_id": "alice",
        "name": "Alice Smith"
    })
    print_response(response, "Create User")
    
    # Test 3: List users
    print("3️⃣ Listing all users...")
    response = requests.get(f"{BASE_URL}/api/users")
    print_response(response, "List Users")
    
    # Test 4: Create database
    print("4️⃣ Creating database 'shop'...")
    response = requests.post(f"{BASE_URL}/api/databases", json={
        "user_id": "alice",
        "db_name": "shop"
    })
    print_response(response, "Create Database")
    
    # Test 5: List databases
    print("5️⃣ Listing databases for user 'alice'...")
    response = requests.get(f"{BASE_URL}/api/databases?user_id=alice")
    print_response(response, "List Databases")
    
    # Test 6: Create table
    print("6️⃣ Creating table 'products'...")
    response = requests.post(
        f"{BASE_URL}/api/databases/alice/shop/tables",
        json={"table_name": "products", "indexes": ["category", "price"]}
    )
    print_response(response, "Create Table")
    
    # Test 7: List tables
    print("7️⃣ Listing tables in database 'shop'...")
    response = requests.get(f"{BASE_URL}/api/databases/alice/shop/tables")
    print_response(response, "List Tables")
    
    # Test 8: Insert records
    print("8️⃣ Inserting product records...")
    products = [
        {"id": "1", "data": {"name": "Laptop", "price": 999.99, "category": "Electronics", "stock": 50}},
        {"id": "2", "data": {"name": "Mouse", "price": 29.99, "category": "Electronics", "stock": 200}},
        {"id": "3", "data": {"name": "Keyboard", "price": 79.99, "category": "Electronics", "stock": 150}},
        {"id": "4", "data": {"name": "Monitor", "price": 299.99, "category": "Electronics", "stock": 80}},
        {"id": "5", "data": {"name": "Desk", "price": 199.99, "category": "Furniture", "stock": 30}},
    ]
    
    for product in products:
        response = requests.post(
            f"{BASE_URL}/api/databases/alice/shop/tables/products/records",
            json=product
        )
        print(f"  ✓ Inserted: {product['data']['name']}")
    
    # Test 9: List all records
    print("\n9️⃣ Listing all product records...")
    response = requests.get(f"{BASE_URL}/api/databases/alice/shop/tables/products/records")
    print_response(response, "List All Records")
    
    # Test 10: Get single record
    print("🔟 Getting product with ID '1'...")
    response = requests.get(f"{BASE_URL}/api/databases/alice/shop/tables/products/records/1")
    print_response(response, "Get Single Record")
    
    # Test 11: Update record
    print("1️⃣1️⃣ Updating product '1' price...")
    response = requests.put(
        f"{BASE_URL}/api/databases/alice/shop/tables/products/records/1",
        json={"data": {"name": "Gaming Laptop", "price": 1299.99, "category": "Electronics", "stock": 45}}
    )
    print_response(response, "Update Record")
    
    # Test 12: Query with filters
    print("1️⃣2️⃣ Querying electronics under $100...")
    response = requests.post(
        f"{BASE_URL}/api/databases/alice/shop/query",
        json={
            "table": "products",
            "filters": [
                {"field": "category", "operator": "eq", "value": "Electronics"},
                {"field": "price", "operator": "lt", "value": 100}
            ],
            "sort": [{"field": "price", "direction": "asc"}]
        }
    )
    print_response(response, "Query with Filters")
    
    # Test 13: Query with pagination
    print("1️⃣3️⃣ Querying with pagination (limit=2, skip=1)...")
    response = requests.get(
        f"{BASE_URL}/api/databases/alice/shop/tables/products/records?limit=2&offset=1"
    )
    print_response(response, "Query with Pagination")
    
    # Test 14: Count query
    print("1️⃣4️⃣ Counting electronics products...")
    response = requests.post(
        f"{BASE_URL}/api/databases/alice/shop/query/count",
        json={
            "table": "products",
            "filters": [
                {"field": "category", "operator": "eq", "value": "Electronics"}
            ]
        }
    )
    print_response(response, "Count Query")
    
    # Test 15: Aggregation query
    print("1️⃣5️⃣ Aggregating products by category...")
    response = requests.post(
        f"{BASE_URL}/api/databases/alice/shop/query/aggregate",
        json={
            "table": "products",
            "group_by": "category",
            "aggregations": {
                "total_value": {"field": "price", "operation": "sum"},
                "avg_price": {"field": "price", "operation": "avg"},
                "count": {"field": "*", "operation": "count"}
            }
        }
    )
    print_response(response, "Aggregation Query")
    
    # Test 16: Get user stats
    print("1️⃣6️⃣ Getting user statistics...")
    response = requests.get(f"{BASE_URL}/api/users/alice/stats")
    print_response(response, "User Statistics")
    
    # Test 17: Delete record
    print("1️⃣7️⃣ Deleting product '5'...")
    response = requests.delete(
        f"{BASE_URL}/api/databases/alice/shop/tables/products/records/5"
    )
    print_response(response, "Delete Record")
    
    print("\n✅ All tests completed!\n")


if __name__ == '__main__':
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("Please start the server first with: python run_api.py\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
