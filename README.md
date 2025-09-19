# NaturalDB
A NoSQL database system capable of storing and querying JSON data while supporting natural language queries.

## Architecture

NaturalDB is built in layers, each providing specific functionality:

### Layer 1: Storage System ✅

The storage system implements a file-based key-value store with the following design:

- **Tables as Folders**: Each table is represented as a directory (e.g., `Products/` for the `Products` table)
- **Records as JSON Files**: Each record is stored as a JSON file (e.g., `Products/1.json` for record with ID `1`)
- **Efficient JSON Storage**: Data is stored in human-readable JSON format with proper indentation

#### Features

- **CRUD Operations**: Create, Read, Update, Delete records
- **Table Management**: Create, list, and drop tables
- **Record Management**: List records, count records, check existence
- **Automatic ID Generation**: UUIDs generated automatically if no ID provided
- **Type Safety**: Full type hints for better development experience

#### Usage Example

```python
from naturaldb.storage import FileStorage

# Initialize storage
storage = FileStorage("data")

# Create a record
product_id = storage.create_record("Products", {
    "name": "Laptop", 
    "price": 999.99, 
    "category": "Electronics"
})

# Read a record
product = storage.read_record("Products", product_id)

# Update a record
storage.update_record("Products", product_id, {
    "name": "Gaming Laptop",
    "price": 1299.99,
    "category": "Electronics"
})

# List all records in a table
product_ids = storage.list_records("Products")

# Delete a record
storage.delete_record("Products", product_id)
```

#### File Structure

The storage system creates a clean directory structure:

```
data/
├── Products/
│   ├── 1.json
│   ├── 2.json
│   └── 3.json
├── Users/
│   ├── user_1.json
│   └── user_2.json
└── Orders/
    ├── order_1.json
    └── order_2.json
```

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the example: `python example.py`
4. Run tests: `pytest tests/`

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
naturaldb/
├── __init__.py
└── storage/
    ├── __init__.py
    └── file_storage.py
tests/
└── test_file_storage.py
```
