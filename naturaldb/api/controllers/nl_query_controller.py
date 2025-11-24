"""
Natural Language Query Controller
Handles natural language query endpoints for NaturalDB
"""

from flask import Blueprint, request, jsonify
from naturaldb.entities import User, Database
from naturaldb.nlp_interface.naturaldb import NaturalDB
import os
from typing import Any, Dict, Tuple, Union

nl_query_bp = Blueprint('nl_query', __name__)


@nl_query_bp.route('', methods=['POST'])
def process_nl_query(user_id: str, db_name: str):
    """
    Process a natural language query.
    
    POST /api/databases/{user_id}/{db_name}/nl-query
    
    Request Body:
        {
            "query": "find all products with price > 100",
            "interactive": false,  // Optional: enable multi-turn conversation
            "max_iterations": 5,   // Optional: max conversation turns
            "context": "..."       // Optional: additional context
        }
    
    Response:
        {
            "success": true,
            "result": {...},
            "message": "Found 42 products",
            "query": "original query text"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing query parameter in request body'
            }), 400
        
        user_query = data['query']
        interactive = data.get('interactive', False)
        max_iterations = data.get('max_iterations', 5)
        context = data.get('context')
        
        # Check if OpenAI API key is available
        if not os.getenv('OPENAI_API_KEY'):
            return jsonify({
                'success': False,
                'error': 'NLP features disabled: OPENAI_API_KEY environment variable not set',
                'message': 'Please configure your OpenAI API key to use natural language queries'
            }), 503
        
        # Create NaturalDB instance
        user = User(id=user_id, name=user_id)
        database = Database(db_name)
        
        try:
            db = NaturalDB(user, database)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to initialize NaturalDB: {str(e)}'
            }), 500
        
        # Check if NLP is enabled
        if not db.nlp_enabled:
            return jsonify({
                'success': False,
                'error': 'NLP features are not available',
                'message': 'Check your OpenAI API key configuration'
            }), 503
        
        # Process the query
        try:
            if interactive:
                result = db.query_interactive(
                    user_query=user_query,
                    context=context,
                    max_iterations=max_iterations
                )
                # Add original query to response
                result['query'] = user_query
                return jsonify(result)
            else:
                result = db.query(
                    user_query=user_query,
                    context=context
                )
                # Add original query to response
                result['query'] = user_query
                return jsonify(result)
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'query': user_query
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Request processing error: {str(e)}'
        }), 400


@nl_query_bp.route('/status', methods=['GET'])
def nl_query_status(user_id: str, db_name: str):
    """
    Check if natural language query features are available.
    
    GET /api/databases/{user_id}/{db_name}/nl-query/status
    
    Response:
        {
            "available": true,
            "model": "gpt-4o-mini",
            "api_key_configured": true,
            "database_summary": "..."
        }
    """
    try:
        # Check API key
        api_key_configured = bool(os.getenv('OPENAI_API_KEY'))
        
        # Try to create NaturalDB instance
        user = User(id=user_id, name=user_id)
        database = Database(db_name)
        
        response = {
            'api_key_configured': api_key_configured,
            'user_id': user_id,
            'database': db_name
        }
        
        if api_key_configured:
            try:
                db = NaturalDB(user, database)
                response['available'] = db.nlp_enabled
                response['model'] = 'gpt-4o-mini'
                
                # Get database summary
                try:
                    response['database_summary'] = db.get_context_summary()
                except Exception:
                    response['database_summary'] = 'Unable to retrieve database summary'
                    
            except Exception as e:
                response['available'] = False
                response['error'] = str(e)
        else:
            response['available'] = False
            response['message'] = 'OpenAI API key not configured'
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'available': False,
            'error': str(e)
        }), 500


@nl_query_bp.route('/examples', methods=['GET'])
def nl_query_examples(user_id: str, db_name: str):
    """
    Get example natural language queries for this database.
    
    GET /api/databases/{user_id}/{db_name}/nl-query/examples
    
    Response:
        {
            "examples": [
                {
                    "query": "find all products with price > 100",
                    "description": "Filter products by price"
                },
                ...
            ]
        }
    """
    examples = [
        {
            "query": "show me all tables",
            "description": "List all available tables in the database"
        },
        {
            "query": "find all products with price > 100",
            "description": "Filter products by price greater than 100"
        },
        {
            "query": "get products with rating >= 4.5 sorted by price",
            "description": "Filter by rating and sort results"
        },
        {
            "query": "show me the top 10 most expensive products",
            "description": "Get top products sorted by price"
        },
        {
            "query": "count how many products have discount > 20",
            "description": "Aggregate query to count products"
        },
        {
            "query": "find products in categories USB Cables or Wall Chargers",
            "description": "Filter by multiple categories using 'in' operator"
        },
        {
            "query": "create a table called favorites with columns: product_id, user_id, created_at",
            "description": "Create a new table with schema"
        },
        {
            "query": "insert a product: name='Wireless Mouse', price=29.99, rating=4.5",
            "description": "Insert a new record"
        },
        {
            "query": "update products set discount=15 where category='USBCables'",
            "description": "Update records matching a condition"
        },
        {
            "query": "delete products where rating < 3.0",
            "description": "Delete records matching a condition"
        }
    ]
    
    return jsonify({
        'database': db_name,
        'user_id': user_id,
        'examples': examples
    })
