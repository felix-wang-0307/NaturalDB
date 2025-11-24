# NaturalDB 🚀  
*A Natural-Language-Driven NoSQL Database System (with E-commerce Demo)*  

🚧 This project is a work in progress and may not be fully functional. 🚧

![architecture](architecture.png)

## Overview  
**NaturalDB** is a custom **NoSQL database system** designed to store and query JSON data while supporting **natural language interaction**.  

Features include:  
- ✅ CRUD operations (Create, Read, Update, Delete)  
- ✅ Advanced queries: filtering, projection, group-by, aggregation, join  
- ✅ Lightweight JSON storage backend  
- ✅ Query engine for structured operations  
- ✅ LLM-powered natural language interface  
- ✅ Security layer for sensitive operations  

For demonstration, we use the [Amazon Sales Dataset](https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset), preprocessed into JSON collections (e.g., `Products`, `Ratings`, `Customers`).  
We also provide a **Next.js e-commerce app** that allows users to browse products, view ratings, and manage orders using **natural language queries**.  

---

## Architecture 🏗️  

### Layer 1: Storage System  
- File-based key-value store.  
- Folders map to tables (e.g., `Products/` = Products collection).  
- Files map to records (e.g., `Products/1.json` = product with ID 1).  
- File-locking for minimal transaction safety.  

### Layer 2: JSON Parser & Query Engine  
- Custom JSON parser (no external `json` library).  
- Query engine supports filtering, projection, group-by, aggregation, join.  

### Layer 3: Natural Language Query Interface  
- LLM module converts natural language → query functions.
  - Example: `"Find orders with rating 5"` → `orders.filter(rating=5)`.
  - Built with **OpenAI Function Calling** for structured outputs.
  - Automatic tool registration from QueryEngine methods.
- Sensitive ops (`update`, `delete`) require confirmation/authorization.
- **Components:**
  - `function_calling.py` - Automatic tool registration system
  - `tool_registry.py` - Database operations to OpenAI tools mapper
  - `nl_query_processor.py` - Natural language to function calls
  - `executor.py` - Execute function calls on QueryEngine
  - `naturaldb.py` - Unified high-level API
- **Usage:**
  ```python
  from naturaldb.nlp_interface import NaturalDB
  from naturaldb.entities import User, Database
  
  db = NaturalDB(User("alice", "Alice"), Database("shop"))
  result = db.query("Show me all products with price > 100")
  ```
- Can be packaged as a reusable **Python library**.  
- See [NLP Interface Documentation](naturaldb/nlp_interface/README.md) for details.
- 

### Layer 4: Front-End Demo (E-commerce)  
- Built with **React**.  
- Users can browse products, view ratings, manage orders.  
- All interactions go through **Flask APIs + NaturalDB**.  
- Demo use-case is e-commerce, but NaturalDB is **application-agnostic**.  

---

## Deployment ☁️  
- **Vercel** used for both backend and frontend deployment.  
- CI/CD pipeline for automated updates.  


---

## Getting Started 💻  

> 🚧 Work in Progress – instructions will be updated as features are built.  

### Prerequisites  
- Python 3.10+  
- Node.js 18+  
- Flask, React, and (optionally) OpenAI API keys  

### Installation  
```bash
# Clone repo
git clone https://github.com/your-username/naturaldb.git
cd naturaldb

# Backend setup
pip install -r requirements.txt

# Set OpenAI API key (required for NLP features)
export OPENAI_API_KEY='your-api-key-here'

# Start backend API server
python run_api.py --port 8080

# Frontend setup
cd frontend
npm install
npm run dev
```

### Using the NLP Interface 🧠

NaturalDB provides a powerful natural language interface for database operations.

#### Python API
```python
from naturaldb.nlp_interface import NaturalDB
from naturaldb.entities import User, Database

# Initialize NaturalDB
db = NaturalDB(User("demo_user", "Demo"), Database("amazon"))

# Simple query
result = db.query("Show me all products with price > 100")

# Interactive mode (multi-turn conversation)
result = db.query_interactive("Find the cheapest product with rating above 4.0")
```

#### REST API
```bash
# Process natural language query
curl -X POST http://localhost:8080/api/databases/demo_user/amazon/nl-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "find all products with rating >= 4.5 sorted by price"
  }'

# Check NLP status
curl http://localhost:8080/api/databases/demo_user/amazon/nl-query/status

# Get example queries
curl http://localhost:8080/api/databases/demo_user/amazon/nl-query/examples
```

#### Demo Script
```bash
# Run NLP demo
python demo_nlp.py
```

### Supported Natural Language Operations

- **Queries**: "find all products with price > 100"
- **Filtering**: "show products with rating >= 4.5"
- **Sorting**: "sort products by price descending"
- **Aggregation**: "count how many products have discount > 20"
- **Multi-category**: "find products in USB Cables or Wall Chargers"
- **Create**: "create a table called favorites"
- **Insert**: "insert a product with name='Mouse', price=29.99"
- **Update**: "update products set discount=15 where category='USBCables'"
- **Delete**: "delete products where rating < 3.0"

---

## API Documentation 📚

### REST Endpoints

- `GET /health` - Health check
- `GET /api/databases` - List all databases
- `GET /api/databases/{user_id}/{db_name}/tables` - List tables
- `GET /api/databases/{user_id}/{db_name}/tables/{table}/records` - Get all records
- `POST /api/databases/{user_id}/{db_name}/query` - Execute structured query
- `POST /api/databases/{user_id}/{db_name}/nl-query` - Natural language query
- `GET /api/databases/{user_id}/{db_name}/nl-query/status` - Check NLP availability
- `GET /api/databases/{user_id}/{db_name}/nl-query/examples` - Get example queries

See [API Documentation](docs/API.md) for full details.

---

## Development 🛠️

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=naturaldb --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Project Structure
```
naturaldb/
├── naturaldb/
│   ├── entities.py           # Core entities (User, Database, Table, Record)
│   ├── storage_system/       # Layer 1: File-based storage
│   ├── query_engine/         # Layer 2: Query operations
│   └── nlp_interface/        # Layer 3: Natural language processing
│       ├── function_calling.py   # Auto tool registration
│       ├── tool_registry.py      # QueryEngine → OpenAI tools
│       ├── nl_query_processor.py # NL → function calls
│       ├── executor.py           # Execute function calls
│       └── naturaldb.py          # Unified API
├── frontend/                 # Layer 4: React frontend
├── data/                     # Database storage
├── tests/                    # Unit tests
├── demo_nlp.py              # NLP interface demo
└── run_api.py               # Flask API server
