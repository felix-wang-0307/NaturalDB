"""
Demo script for NaturalDB Layer 3 - Natural Language Interface
Demonstrates how to use natural language queries with NaturalDB.
"""

from naturaldb.entities import User, Database, Table, Record
from naturaldb.nlp_interface.naturaldb import NaturalDB
from naturaldb.env_config import config
import os


def demo_basic_usage():
    """Demonstrate basic natural language queries."""
    print("=" * 60)
    print("NaturalDB Layer 3 Demo - Natural Language Interface")
    print("=" * 60)
    
    # Initialize NaturalDB
    user = User(id="demo_user", name="Demo User")
    database = Database(name="demo_db")
    
    # Check if OpenAI API key is set
    if not config.get_openai_api_key():
        print("\n⚠️  Warning: OPENAI_API_KEY not configured!")
        print("Natural language features will be disabled.")
        print("Please set it in naturaldb/.env file:")
        print("  OPENAI_API_KEY=your-api-key\n")
        return
    
    db = NaturalDB(user, database)
    
    print(f"\n📊 Database Context:\n{db.get_context()}")
    
    # Example 1: Create a table
    print("\n" + "=" * 60)
    print("Example 1: Create a table using natural language")
    print("=" * 60)
    
    query1 = "Create a table called products"
    print(f"\n🗣️  Query: {query1}")
    
    result1 = db.query(query1)
    print(f"✅ Result: {result1}")
    
    # Example 2: Insert data
    print("\n" + "=" * 60)
    print("Example 2: Insert product data")
    print("=" * 60)
    
    query2 = "Insert a product with id '1' and data: name='Laptop', price=999, category='Electronics'"
    print(f"\n🗣️  Query: {query2}")
    
    result2 = db.query(query2)
    print(f"✅ Result: {result2}")
    
    # Example 3: Query data
    print("\n" + "=" * 60)
    print("Example 3: Find products")
    print("=" * 60)
    
    query3 = "Show me all products"
    print(f"\n🗣️  Query: {query3}")
    
    result3 = db.query(query3)
    print(f"✅ Result: {result3}")
    
    # Example 4: Filter data
    print("\n" + "=" * 60)
    print("Example 4: Filter products by price")
    print("=" * 60)
    
    query4 = "Find products with price greater than 500"
    print(f"\n🗣️  Query: {query4}")
    
    result4 = db.query(query4)
    print(f"✅ Result: {result4}")
    
    # Example 5: Interactive query (multi-turn)
    print("\n" + "=" * 60)
    print("Example 5: Interactive query with multiple operations")
    print("=" * 60)
    
    query5 = "Add a few more products and then show me the cheapest one"
    print(f"\n🗣️  Query: {query5}")
    
    result5 = db.query_interactive(query5)
    print(f"✅ Result: {result5}")


def demo_without_openai():
    """Demonstrate NaturalDB can still work without OpenAI API."""
    print("\n" + "=" * 60)
    print("Demo: Using NaturalDB without OpenAI API")
    print("=" * 60)
    
    user = User(id="local_user", name="Local User")
    database = Database(name="local_db")
    
    # This will work even without OpenAI API key
    db = NaturalDB(user, database)
    
    print(f"\nNLP Enabled: {db.nlp_enabled}")
    print("You can still use the query engine directly:")
    
    # Direct access to query engine
    table = Table(name="users", indexes={})
    db.engine.create_table(table)
    
    record = Record(id="1", data={"name": "Alice", "age": 30})
    db.engine.insert("users", record)
    
    results = db.engine.find_all("users")
    print(f"\nUsers: {[{'id': r.id, 'data': r.data} for r in results]}")


def demo_confirmation_callback():
    """Demonstrate sensitive operations with confirmation callback."""
    print("\n" + "=" * 60)
    print("Demo: Sensitive Operations with Confirmation")
    print("=" * 60)
    
    def confirmation_handler(operation: str, args: dict) -> bool:
        """Ask user for confirmation."""
        print(f"\n⚠️  Confirmation required for {operation}!")
        print(f"Arguments: {args}")
        response = input("Proceed? (yes/no): ")
        return response.lower() in ['yes', 'y']
    
    user = User(id="safe_user", name="Safe User")
    database = Database(name="safe_db")
    
    db = NaturalDB(
        user,
        database,
        confirmation_callback=confirmation_handler
    )
    
    # This would trigger confirmation
    query = "Delete the product with id '1'"
    print(f"\n🗣️  Query: {query}")
    
    result = db.query(query)
    print(f"✅ Result: {result}")


if __name__ == "__main__":
    # Run basic demo
    demo_basic_usage()
    
    # Show it works without OpenAI too
    demo_without_openai()
    
    # Show confirmation callback
    # Uncomment to test:
    # demo_confirmation_callback()
