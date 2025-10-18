#!/usr/bin/env python3
"""
NaturalDB Layer 2 Query Engine Demo
This script demonstrates the basic and advanced query capabilities of the NaturalDB query engine.
"""

import os
import sys

# Add the parent directory to sys.path to import naturaldb modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from naturaldb.entities import User, Database, Table, Record
from naturaldb.query_engine import QueryEngine, JSONParser


def demo_basic_operations():
    """Demonstrate basic CRUD operations"""
    print("=== Demo: Basic CRUD Operations ===")
    
    # Initialize query engine
    user = User(id="demo_user", name="Demo User")
    database = Database(name="demo_db")
    query_engine = QueryEngine(user, database)
    
    print("1. Creating sample data...")
    
    # Create some sample products
    products = [
        Record(id="1", data={
            "id": 1,
            "name": "iPhone 15",
            "price": 899.99,
            "category": "Electronics",
            "in_stock": True,
            "specs": {"storage": "128GB", "color": "Blue"}
        }),
        Record(id="2", data={
            "id": 2,
            "name": "Samsung Galaxy S24",
            "price": 799.99,
            "category": "Electronics",
            "in_stock": True,
            "specs": {"storage": "256GB", "color": "Black"}
        }),
        Record(id="3", data={
            "id": 3,
            "name": "MacBook Air",
            "price": 1199.99,
            "category": "Computers",
            "in_stock": False,
            "specs": {"storage": "512GB", "color": "Silver"}
        })
    ]
    
    # Insert products
    for product in products:
        success = query_engine.insert("Products", product)
        print(f"   Inserted product {product.id}: {success}")
    
    print("\n2. Reading data...")
    
    # Read all products
    all_products = query_engine.find_all("Products")
    print(f"   Found {len(all_products)} products")
    
    # Read specific product
    product = query_engine.find_by_id("Products", "1")
    if product:
        print(f"   Product 1: {product.data['name']} - ${product.data['price']}")
    
    print("\n3. Updating data...")
    
    # Update product price
    if product:
        product.data['price'] = 849.99
        success = query_engine.update("Products", product)
        print(f"   Updated product 1 price: {success}")
    
    print("\n4. Filtering data...")
    
    # Filter by category
    electronics = query_engine.filter("Products", "category", "Electronics")
    print(f"   Electronics products: {len(electronics)}")
    
    # Filter by price range
    operations = query_engine.get_table_operations("Products")
    if operations:
        expensive_products = operations.filter_by_field("price", 900, "gt")
        print(f"   Products over $900: {len(expensive_products)}")
    
    print("\n5. Deleting data...")
    
    # Delete a product
    success = query_engine.delete("Products", "3")
    print(f"   Deleted product 3: {success}")
    
    # Verify deletion
    remaining = query_engine.find_all("Products")
    print(f"   Remaining products: {len(remaining)}")


def demo_advanced_queries():
    """Demonstrate advanced query operations"""
    print("\n=== Demo: Advanced Query Operations ===")
    
    user = User(id="demo_user", name="Demo User")
    database = Database(name="demo_db")
    query_engine = QueryEngine(user, database)
    
    print("1. Projection (selecting specific fields)...")
    
    # Project specific fields
    projected = query_engine.project("Products", ["name", "price", "specs.color"])
    for item in projected:
        print(f"   {item}")
    
    print("\n2. Sorting...")
    
    # Sort by price
    sorted_products = query_engine.sort("Products", "price", ascending=False)
    for product in sorted_products:
        print(f"   {product.data['name']}: ${product.data['price']}")
    
    print("\n3. Grouping and Aggregation...")
    
    # Add more products for grouping demo
    more_products = [
        Record(id="4", data={"id": 4, "name": "iPad", "price": 599.99, "category": "Electronics"}),
        Record(id="5", data={"id": 5, "name": "Dell Laptop", "price": 899.99, "category": "Computers"}),
    ]
    
    for product in more_products:
        query_engine.insert("Products", product)
    
    # Group by category with aggregations
    grouped = query_engine.group_by("Products", "category", {
        "price": "avg",
        "price": "max"
    })
    
    for category, stats in grouped.items():
        print(f"   {category}: {stats}")


def demo_joins():
    """Demonstrate join operations"""
    print("\n=== Demo: Join Operations ===")
    
    user = User(id="demo_user", name="Demo User")
    database = Database(name="demo_db")
    query_engine = QueryEngine(user, database)
    
    print("1. Creating Orders table...")
    
    # Create some orders
    orders = [
        Record(id="1", data={"id": 1, "user_id": 1, "product_id": 1, "quantity": 1, "total": 849.99}),
        Record(id="2", data={"id": 2, "user_id": 2, "product_id": 2, "quantity": 2, "total": 1599.98}),
        Record(id="3", data={"id": 3, "user_id": 1, "product_id": 4, "quantity": 1, "total": 599.99}),
    ]
    
    for order in orders:
        query_engine.insert("Orders", order)
    
    print("2. Performing inner join between Orders and Products...")
    
    # Join orders with products
    joined = query_engine.join(
        "Orders", "Products",
        "product_id", "id",
        join_type="inner",
        left_alias="order",
        right_alias="product"
    )
    
    for result in joined:
        order_data = result["order"]
        product_data = result["product"]
        print(f"   Order {order_data['id']}: {product_data['name']} x{order_data['quantity']} = ${order_data['total']}")


def demo_json_parser():
    """Demonstrate custom JSON parser"""
    print("\n=== Demo: Custom JSON Parser ===")
    
    print("1. Parsing JSON string...")
    
    json_str = '''
    {
        "name": "Test Product",
        "price": 99.99,
        "features": ["feature1", "feature2"],
        "available": true,
        "metadata": null
    }
    '''
    
    parsed = JSONParser.parse_string(json_str)
    print(f"   Parsed: {parsed}")
    
    print("\n2. Converting to JSON string...")
    
    data = {
        "id": 1,
        "name": "Example",
        "values": [1, 2, 3],
        "nested": {"key": "value"}
    }
    
    json_output = JSONParser.to_json_string(data, indent=2)
    print(f"   JSON output:\n{json_output}")
    
    print("\n3. Parsing demo data file...")
    
    try:
        demo_file = "/Users/waterdog/git/DSCI-551/project/code/demo_data/Products/1.json"
        if os.path.exists(demo_file):
            parsed_file = JSONParser.parse_file(demo_file)
            print(f"   Demo file content: {parsed_file}")
        else:
            print("   Demo file not found")
    except Exception as e:
        print(f"   Error reading demo file: {e}")


def demo_import_export():
    """Demonstrate import/export functionality"""
    print("\n=== Demo: Import/Export Functionality ===")
    
    user = User(id="demo_user", name="Demo User")
    database = Database(name="demo_db")
    query_engine = QueryEngine(user, database)
    
    print("1. Importing from demo data...")
    
    # Try to import from demo data files
    demo_products_file = "/Users/waterdog/git/DSCI-551/project/code/demo_data/Products/1.json"
    if os.path.exists(demo_products_file):
        success = query_engine.import_from_json_file("ImportedProducts", demo_products_file)
        print(f"   Import success: {success}")
        
        if success:
            imported = query_engine.find_all("ImportedProducts")
            print(f"   Imported {len(imported)} records")
    
    print("\n2. Exporting to file...")
    
    # Export products to a new file
    export_file = "/tmp/exported_products.json"
    try:
        success = query_engine.export_to_json_file("Products", export_file)
        print(f"   Export success: {success}")
        
        if success and os.path.exists(export_file):
            with open(export_file, 'r') as f:
                content = f.read()[:200]  # First 200 characters
                print(f"   Exported content preview: {content}...")
    except Exception as e:
        print(f"   Export error: {e}")


def main():
    """Run all demos"""
    print("NaturalDB Layer 2 Query Engine Demo")
    print("=" * 50)
    
    try:
        demo_basic_operations()
        demo_advanced_queries()
        demo_joins()
        demo_json_parser()
        demo_import_export()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        
        # Show available tables
        user = User(id="demo_user", name="Demo User")
        database = Database(name="demo_db")
        query_engine = QueryEngine(user, database)
        tables = query_engine.list_tables()
        print(f"Available tables: {tables}")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()