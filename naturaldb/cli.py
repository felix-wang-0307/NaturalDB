#!/usr/bin/env python3
"""
NaturalDB Command Line Interface for Layer 1 Storage System

Basic CLI for interacting with the file-based storage system.
"""

import argparse
import json
import sys
from naturaldb import Storage


def create_table(storage, table_name):
    """Create a new table"""
    if storage.create_table(table_name):
        print(f"✅ Created table '{table_name}'")
    else:
        print(f"❌ Table '{table_name}' already exists")


def list_tables(storage):
    """List all tables"""
    tables = storage.list_tables()
    if tables:
        print("📁 Tables:")
        for table in sorted(tables):
            count = storage.count_records(table)
            print(f"   {table} ({count} records)")
    else:
        print("No tables found")


def drop_table(storage, table_name):
    """Drop a table"""
    if storage.drop_table(table_name):
        print(f"✅ Dropped table '{table_name}'")
    else:
        print(f"❌ Table '{table_name}' not found")


def insert_record(storage, table_name, record_id, data_json):
    """Insert a record"""
    try:
        data = json.loads(data_json)
        storage.insert(table_name, record_id, data)
        print(f"✅ Inserted record '{record_id}' in table '{table_name}'")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
    except Exception as e:
        print(f"❌ Error inserting record: {e}")


def get_record(storage, table_name, record_id):
    """Get a record"""
    try:
        data = storage.get(table_name, record_id)
        if data is not None:
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Record '{record_id}' not found in table '{table_name}'")
    except Exception as e:
        print(f"❌ Error retrieving record: {e}")


def list_records(storage, table_name):
    """List records in a table"""
    try:
        records = storage.list_records(table_name)
        if records:
            print(f"📄 Records in '{table_name}':")
            for record_id in sorted(records):
                print(f"   {record_id}")
        else:
            print(f"No records found in table '{table_name}'")
    except Exception as e:
        print(f"❌ Error listing records: {e}")


def update_record(storage, table_name, record_id, data_json):
    """Update a record"""
    try:
        data = json.loads(data_json)
        storage.update(table_name, record_id, data)
        print(f"✅ Updated record '{record_id}' in table '{table_name}'")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
    except Exception as e:
        print(f"❌ Error updating record: {e}")


def delete_record(storage, table_name, record_id):
    """Delete a record"""
    if storage.delete(table_name, record_id):
        print(f"✅ Deleted record '{record_id}' from table '{table_name}'")
    else:
        print(f"❌ Record '{record_id}' not found in table '{table_name}'")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="NaturalDB Layer 1 Storage System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Table operations
  naturaldb-cli --create-table Products
  naturaldb-cli --list-tables
  naturaldb-cli --drop-table Products

  # Record operations
  naturaldb-cli --insert Products 1 '{"name": "iPhone", "price": 999}'
  naturaldb-cli --get Products 1
  naturaldb-cli --list-records Products
  naturaldb-cli --update Products 1 '{"name": "iPhone 15", "price": 899}'
  naturaldb-cli --delete Products 1
        """
    )
    
    parser.add_argument("--storage-path", default="data", 
                       help="Storage directory path (default: data)")
    
    # Table operations
    parser.add_argument("--create-table", metavar="TABLE",
                       help="Create a new table")
    parser.add_argument("--list-tables", action="store_true",
                       help="List all tables")
    parser.add_argument("--drop-table", metavar="TABLE",
                       help="Drop a table")
    
    # Record operations
    parser.add_argument("--insert", nargs=3, metavar=("TABLE", "ID", "JSON"),
                       help="Insert a record")
    parser.add_argument("--get", nargs=2, metavar=("TABLE", "ID"),
                       help="Get a record")
    parser.add_argument("--list-records", metavar="TABLE",
                       help="List records in a table")
    parser.add_argument("--update", nargs=3, metavar=("TABLE", "ID", "JSON"),
                       help="Update a record")
    parser.add_argument("--delete", nargs=2, metavar=("TABLE", "ID"),
                       help="Delete a record")
    
    args = parser.parse_args()
    
    # Check if any operation was specified
    operations = [
        args.create_table, args.list_tables, args.drop_table,
        args.insert, args.get, args.list_records, args.update, args.delete
    ]
    
    if not any(operations):
        parser.print_help()
        return
    
    # Initialize storage
    with Storage(args.storage_path) as storage:
        # Execute operations
        if args.create_table:
            create_table(storage, args.create_table)
        
        if args.list_tables:
            list_tables(storage)
        
        if args.drop_table:
            drop_table(storage, args.drop_table)
        
        if args.insert:
            table, record_id, data_json = args.insert
            insert_record(storage, table, record_id, data_json)
        
        if args.get:
            table, record_id = args.get
            get_record(storage, table, record_id)
        
        if args.list_records:
            list_records(storage, args.list_records)
        
        if args.update:
            table, record_id, data_json = args.update
            update_record(storage, table, record_id, data_json)
        
        if args.delete:
            table, record_id = args.delete
            delete_record(storage, table, record_id)


if __name__ == "__main__":
    main()