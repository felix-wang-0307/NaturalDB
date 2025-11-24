"""
Query Controller
Handles advanced query operations using chainable API
"""

from flask import Blueprint, request, jsonify
from ...entities import User, Database
from ...query_engine.query_engine import QueryEngine

query_bp = Blueprint('query', __name__)


@query_bp.route('/', methods=['POST'])
def execute_query(user_id, db_name):
    """
    Execute an advanced query using DSL
    
    Request body:
        {
            "table": "table_name",           // required
            "filters": [                     // optional
                {"field": "age", "operator": "gt", "value": 30},
                {"field": "status", "operator": "eq", "value": "active"}
            ],
            "sort": [                        // optional
                {"field": "name", "direction": "asc"},
                {"field": "age", "direction": "desc"}
            ],
            "limit": 10,                     // optional
            "skip": 0,                       // optional
            "project": ["name", "age"],      // optional
            "group_by": "category",          // optional
            "aggregate": {                   // optional (only with group_by)
                "total": {"field": "price", "operation": "sum"}
            }
        }
    
    Returns:
        {
            "success": true,
            "count": 5,
            "results": [...]
        }
    """
    data = request.get_json()
    
    if not data or 'table' not in data:
        return jsonify({'error': 'table is required'}), 400
    
    table_name = data['table']
    
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        engine = QueryEngine(user, database)
        
        # Build query chain
        query = engine.table(table_name)
        
        # Apply filters
        if 'filters' in data:
            for filter_spec in data['filters']:
                field = filter_spec.get('field')
                operator = filter_spec.get('operator', 'eq')
                value = filter_spec.get('value')
                
                if field and value is not None:
                    query = query.filter_by(field, value, operator)
        
        # Apply sorting
        if 'sort' in data:
            for sort_spec in data['sort']:
                field = sort_spec.get('field')
                direction = sort_spec.get('direction', 'asc')
                
                if field:
                    reverse = (direction.lower() == 'desc')
                    query = query.sort(field, reverse)
        
        # Apply skip/limit
        if 'skip' in data:
            query = query.skip(data['skip'])
        
        if 'limit' in data:
            query = query.limit(data['limit'])
        
        # Execute based on operation type
        if 'group_by' in data:
            # Group by operation
            group_field = data['group_by']
            aggregations = data.get('aggregate', {})
            
            # First get all records matching filters
            all_records = query.all()
            
            # Group by field
            from ...query_engine.operations import QueryOperations
            grouped = QueryOperations.group_by(all_records, group_field)
            
            # Apply aggregations to each group
            results = []
            for group_value, group_records in grouped.items():
                result = {group_field: group_value}
                
                for agg_name, agg_spec in aggregations.items():
                    field = agg_spec.get('field')
                    operation = agg_spec.get('operation', 'sum')
                    
                    if field and field != '*':
                        result[agg_name] = QueryOperations.aggregate(group_records, field, operation)
                    elif operation == 'count':
                        result[agg_name] = len(group_records)
                
                results.append(result)
            
        elif 'project' in data:
            # Projection operation
            results = query.project(data['project'])
            
        else:
            # Regular query
            results = query.all()
        
        # Convert to dict format
        if results:
            if isinstance(results, list) and len(results) > 0:
                first_item = results[0]
                if hasattr(first_item, 'id') and hasattr(first_item, 'data'):
                    # Records - convert to dicts
                    from ...entities import Record
                    results_list = [{'id': r.id, **r.data} if isinstance(r, Record) else r for r in results]
                else:
                    # Already dicts (from group_by or project)
                    results_list = results
            else:
                results_list = results
        else:
            results_list = []
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'db_name': db_name,
            'table': table_name,
            'count': len(results_list),
            'results': results_list
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@query_bp.route('/count', methods=['POST'])
def count_query(user_id, db_name):
    """
    Count records matching query criteria
    
    Request body:
        {
            "table": "table_name",           // required
            "filters": [...]                 // optional
        }
    """
    data = request.get_json()
    
    if not data or 'table' not in data:
        return jsonify({'error': 'table is required'}), 400
    
    table_name = data['table']
    
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        engine = QueryEngine(user, database)
        
        # Build query chain
        query = engine.table(table_name)
        
        # Apply filters
        if 'filters' in data:
            for filter_spec in data['filters']:
                field = filter_spec.get('field')
                operator = filter_spec.get('operator', 'eq')
                value = filter_spec.get('value')
                
                if field and value is not None:
                    query = query.filter_by(field, value, operator)
        
        count = query.count()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'db_name': db_name,
            'table': table_name,
            'count': count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@query_bp.route('/aggregate', methods=['POST'])
def aggregate_query(user_id, db_name):
    """
    Perform aggregation operations
    
    Request body:
        {
            "table": "table_name",           // required
            "group_by": "category",          // required
            "aggregations": {                // required
                "total": {"field": "price", "operation": "sum"},
                "average": {"field": "price", "operation": "avg"},
                "count": {"field": "*", "operation": "count"}
            },
            "filters": [...]                 // optional
        }
    """
    data = request.get_json()
    
    if not data or 'table' not in data or 'group_by' not in data or 'aggregations' not in data:
        return jsonify({'error': 'table, group_by, and aggregations are required'}), 400
    
    table_name = data['table']
    group_field = data['group_by']
    aggregations = data['aggregations']
    
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        engine = QueryEngine(user, database)
        
        # Build query chain
        query = engine.table(table_name)
        
        # Apply filters
        if 'filters' in data:
            for filter_spec in data['filters']:
                field = filter_spec.get('field')
                operator = filter_spec.get('operator', 'eq')
                value = filter_spec.get('value')
                
                if field and value is not None:
                    query = query.filter_by(field, value, operator)
        
        # Get all records matching filters
        all_records = query.all()
        
        # Group by field
        from ...query_engine.operations import QueryOperations
        grouped = QueryOperations.group_by(all_records, group_field)
        
        # Apply aggregations to each group
        results = []
        for group_value, group_records in grouped.items():
            result = {group_field: group_value}
            
            for agg_name, agg_spec in aggregations.items():
                field = agg_spec.get('field')
                operation = agg_spec.get('operation', 'sum')
                
                if field and field != '*':
                    result[agg_name] = QueryOperations.aggregate(group_records, field, operation)
                elif operation == 'count':
                    result[agg_name] = len(group_records)
            
            results.append(result)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'db_name': db_name,
            'table': table_name,
            'group_by': group_field,
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
