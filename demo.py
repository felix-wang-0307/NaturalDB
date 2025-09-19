#!/usr/bin/env python3
"""
NaturalDB Layer 1 Storage System Demo

This script demonstrates the file-based storage system capabilities
as described in the README.md architecture.
"""

from naturaldb import Storage
import json
from pathlib import Path


def demo_basic_operations():
    """Demonstrate basic CRUD operations"""
    print("=" * 60)
    print("NaturalDB Layer 1 Storage System Demo")
    print("=" * 60)
    
    # Initialize storage system
    with Storage("demo_data") as storage:
        print("✅ Initialized file-based storage system")
        
        # Create tables (folders)
        storage.create_table("Products")
        storage.create_table("Users")
        storage.create_table("Orders")
        print("✅ Created tables: Products, Users, Orders")
        
        # Insert sample products
        products = [
            {
                "id": 1,
                "name": "iPhone 15",
                "price": 999.99,
                "category": "Electronics",
                "in_stock": True,
                "specs": {
                    "storage": "128GB",
                    "color": "Blue",
                    "screen_size": 6.1
                }
            },
            {
                "id": 2,
                "name": "MacBook Pro",
                "price": 1999.99,
                "category": "Computers",
                "in_stock": True,
                "specs": {
                    "ram": "16GB",
                    "storage": "512GB SSD",
                    "chip": "M3 Pro"
                }
            },
            {
                "id": 3,
                "name": "AirPods Pro",
                "price": 249.99,
                "category": "Audio",
                "in_stock": False,
                "specs": {
                    "noise_cancelling": True,
                    "battery_life": "6 hours"
                }
            }
        ]
        
        for product in products:
            storage.insert("Products", product["id"], product)
        print(f"✅ Inserted {len(products)} products")
        
        # Insert sample users
        users = [
            {
                "id": 1,
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "preferences": {
                    "category": "Electronics",
                    "max_price": 1500
                }
            },
            {
                "id": 2,
                "name": "Bob Smith",
                "email": "bob@example.com",
                "preferences": {
                    "category": "Computers",
                    "max_price": 2500
                }
            }
        ]
        
        for user in users:
            storage.insert("Users", user["id"], user)
        print(f"✅ Inserted {len(users)} users")
        
        # Insert sample orders
        orders = [
            {
                "id": 1,
                "user_id": 1,
                "product_id": 1,
                "quantity": 1,
                "total": 999.99,
                "status": "completed",
                "order_date": "2024-01-15"
            },
            {
                "id": 2,
                "user_id": 2,
                "product_id": 2,
                "quantity": 1,
                "total": 1999.99,
                "status": "pending",
                "order_date": "2024-01-16"
            }
        ]
        
        for order in orders:
            storage.insert("Orders", order["id"], order)
        print(f"✅ Inserted {len(orders)} orders")
        
        print("\n" + "=" * 60)
        print("Storage System Status")
        print("=" * 60)
        
        # Show table information
        tables = storage.list_tables()
        print(f"📁 Tables: {', '.join(tables)}")
        
        for table in tables:
            count = storage.count_records(table)
            print(f"   {table}: {count} records")
        
        print("\n" + "=" * 60)
        print("Sample Data Retrieval")
        print("=" * 60)
        
        # Retrieve and display some records
        print("📦 Product 1:")
        product1 = storage.get("Products", 1)
        print(json.dumps(product1, indent=2))
        
        print("\n👤 User 1:")
        user1 = storage.get("Users", 1)
        print(json.dumps(user1, indent=2))
        
        print("\n📋 Order 1:")
        order1 = storage.get("Orders", 1)
        print(json.dumps(order1, indent=2))
        
        print("\n" + "=" * 60)
        print("Update Operation Example")
        print("=" * 60)
        
        # Update product price
        product1["price"] = 899.99
        product1["on_sale"] = True
        storage.update("Products", 1, product1)
        
        updated_product = storage.get("Products", 1)
        print("📦 Updated Product 1 price:")
        print(f"   Price: ${updated_product['price']}")
        print(f"   On Sale: {updated_product['on_sale']}")
        
        print("\n" + "=" * 60)
        print("File System Structure")
        print("=" * 60)
        
        # Show the actual file structure
        print("📂 File system layout:")
        demo_path = Path("demo_data")
        if demo_path.exists():
            for item in sorted(demo_path.rglob("*")):
                if item.is_file():
                    relative_path = item.relative_to(demo_path)
                    print(f"   📄 {relative_path}")
                elif item.is_dir() and item != demo_path:
                    relative_path = item.relative_to(demo_path)
                    print(f"   📁 {relative_path}/")
        
        print("\n" + "=" * 60)
        print("Demo Complete!")
        print("=" * 60)
        print("Layer 1 Storage System successfully demonstrated:")
        print("✅ File-based key-value store")
        print("✅ Folders map to tables (Products/, Users/, Orders/)")
        print("✅ Files map to records (1.json, 2.json, etc.)")
        print("✅ File-locking for transaction safety")
        print("✅ Full CRUD operations")
        print("✅ Complex nested JSON data support")


if __name__ == "__main__":
    demo_basic_operations()