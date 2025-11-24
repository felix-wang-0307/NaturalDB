#!/usr/bin/env python3
"""
Demo script for testing the NaturalDB NLP interface

Run this script to test natural language queries:
    python demo_nlp.py
"""

import os
from dotenv import load_dotenv
from naturaldb.entities import User, Database
from naturaldb.nlp_interface.naturaldb import NaturalDB

# Load environment variables from .env file
load_dotenv()


def main():
    print("=" * 60)
    print("🧠 NaturalDB - Natural Language Interface Demo")
    print("=" * 60)
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("\n⚠️  Warning: OPENAI_API_KEY not set!")
        print("Set your OpenAI API key to use NLP features:")
        print("  export OPENAI_API_KEY='your-api-key-here'\n")
        return
    
    # Initialize NaturalDB
    user = User(id="demo_user", name="Demo User")
    database = Database("amazon")
    
    print(f"\n📊 Connecting to database: {user.id}/{database.name}")
    
    try:
        db = NaturalDB(user, database)
        
        if not db.nlp_enabled:
            print("\n❌ NLP features are not available")
            return
        
        print("✅ NLP interface initialized successfully!\n")
        
        # Show database summary
        print("📋 Database Summary:")
        print("-" * 60)
        print(db.get_context_summary())
        print("-" * 60)
        
        # Example queries
        queries = [
            "show me all tables",
            "find 5 products with price > 100",
            "get products with rating >= 4.5 sorted by price descending",
            "count how many products are in the USBCables category"
        ]
        
        print("\n🔍 Example Queries:")
        print("-" * 60)
        
        for i, query in enumerate(queries, 1):
            print(f"\n{i}. Query: \"{query}\"")
            print("   " + "─" * 50)
            
            try:
                result = db.query(query)
                
                if result['success']:
                    print(f"   ✅ {result.get('message', 'Success')}")
                    
                    if result.get('result'):
                        # Show result preview
                        res = result['result']
                        if isinstance(res, list):
                            print(f"   📦 Results: {len(res)} items")
                            if res and len(res) <= 3:
                                for item in res:
                                    print(f"      - {item}")
                        elif isinstance(res, dict):
                            print(f"   📦 Result: {res}")
                        else:
                            print(f"   📦 Result: {res}")
                else:
                    print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
        
        print("\n" + "-" * 60)
        
        # Interactive mode demo (disabled due to token limits with large datasets)
        print("\n🔄 Interactive Mode Demo (Skipped):")
        print("-" * 60)
        print("Note: Interactive mode disabled for large datasets to avoid token limits.")
        print("For production use, consider using gpt-4o-mini with smaller result sets.")
        
        # Example of a simple non-interactive query instead
        print("\n🔍 Simple Query Demo:")
        print("-" * 60)
        try:
            result = db.query("How many tables are in the database?")
            if result['success']:
                print(f"✅ {result.get('message', 'Success')}")
                if result.get('result'):
                    print(f"   📦 Result: {result['result']}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        print("\n" + "=" * 60)
        print("✨ Demo completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error initializing NaturalDB: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
