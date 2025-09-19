#!/usr/bin/env python3
"""
Example usage of NaturalDB's Layer 1: Storage System.

This script demonstrates the file-based key-value storage system.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from naturaldb.storage import FileStorage


def main():
    """Demonstrate the FileStorage functionality."""
    print("=== NaturalDB Layer 1: Storage System Demo ===\n")
    
    # Initialize storage with a demo data directory
    storage = FileStorage("demo_data")
    
    print("1. Creating sample records in 'Products' table...")
    
    # Create some sample products
    products = [
        {"name": "Laptop", "price": 999.99, "category": "Electronics", "stock": 50},
        {"name": "Coffee Mug", "price": 12.99, "category": "Kitchen", "stock": 100},
        {"name": "Book", "price": 24.99, "category": "Education", "stock": 75},
    ]
    
    product_ids = []
    for i, product in enumerate(products, 1):
        product_id = storage.create_record("Products", product, str(i))
        product_ids.append(product_id)
        print(f"   Created product with ID: {product_id}")
    
    print(f"\n2. Current tables: {storage.list_tables()}")
    print(f"   Records in Products table: {storage.list_records('Products')}")
    print(f"   Total products: {storage.get_record_count('Products')}")
    
    print("\n3. Reading individual records...")
    for product_id in product_ids:
        product = storage.read_record("Products", product_id)
        print(f"   Product {product_id}: {product['name']} - ${product['price']}")
    
    print("\n4. Updating a record...")
    updated_data = {
        "name": "Gaming Laptop", 
        "price": 1299.99, 
        "category": "Electronics", 
        "stock": 25,
        "features": ["RGB Keyboard", "High Refresh Rate", "Dedicated GPU"]
    }
    success = storage.update_record("Products", "1", updated_data)
    if success:
        updated_product = storage.read_record("Products", "1")
        print(f"   Updated product 1: {updated_product['name']} - ${updated_product['price']}")
        print(f"   New features: {updated_product['features']}")
    
    print("\n5. Creating records in different tables...")
    
    # Create users
    users = [
        {"name": "Alice Johnson", "email": "alice@example.com", "age": 28},
        {"name": "Bob Smith", "email": "bob@example.com", "age": 35},
    ]
    
    for i, user in enumerate(users, 1):
        user_id = storage.create_record("Users", user, f"user_{i}")
        print(f"   Created user: {user['name']} (ID: {user_id})")
    
    # Create orders
    orders = [
        {"user_id": "user_1", "product_ids": ["1", "3"], "total": 1324.98, "status": "completed"},
        {"user_id": "user_2", "product_ids": ["2"], "total": 12.99, "status": "pending"},
    ]
    
    for i, order in enumerate(orders, 1):
        order_id = storage.create_record("Orders", order, f"order_{i}")
        print(f"   Created order: {order_id} (Total: ${order['total']})")
    
    print(f"\n6. All tables: {storage.list_tables()}")
    for table in storage.list_tables():
        count = storage.get_record_count(table)
        print(f"   {table}: {count} records")
    
    print("\n7. Demonstrating file structure...")
    print("   The storage system creates the following structure:")
    print("   demo_data/")
    print("   ├── Products/")
    print("   │   ├── 1.json")
    print("   │   ├── 2.json")
    print("   │   └── 3.json")
    print("   ├── Users/")
    print("   │   ├── user_1.json")
    print("   │   └── user_2.json")
    print("   └── Orders/")
    print("       ├── order_1.json")
    print("       └── order_2.json")
    
    print("\n8. Cleaning up (deleting a record)...")
    success = storage.delete_record("Products", "2")
    if success:
        print("   Deleted product 2 (Coffee Mug)")
        print(f"   Remaining products: {storage.list_records('Products')}")
    
    print("\n=== Demo completed! ===")
    print(f"Check the 'demo_data' directory to see the generated files.")


if __name__ == "__main__":
    main()