"""
Record Controller
Handles record CRUD operations
"""

from flask import Blueprint, request, jsonify
from ...entities import User, Database, Record
from ...query_engine.query_engine import QueryEngine

record_bp = Blueprint('record', __name__)


@record_bp.route('/', methods=['GET'])
def list_records(user_id, db_name, table_name):
    """
    List all records in a table
    
    Query params:
        limit: Max number of records to return
        offset: Number of records to skip
    """
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int, default=0)
    
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        engine = QueryEngine(user, database)
        
        records = engine.find_all(table_name)
        
        # Apply pagination
        if limit:
            records = records[offset:offset+limit]
        elif offset:
            records = records[offset:]
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'db_name': db_name,
            'table_name': table_name,
            'total': len(engine.find_all(table_name)),
            'count': len(records),
            'records': [{'id': r.id, **r.data} for r in records]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@record_bp.route('/', methods=['POST'])
def create_record(user_id, db_name, table_name):
    """
    Create a new record
    
    Request body:
        {
            "id": "string",  // required
            "data": {}       // required
        }
    """
    data = request.get_json()
    
    if not data or 'id' not in data or 'data' not in data:
        return jsonify({'error': 'id and data are required'}), 400
    
    record_id = data['id']
    record_data = data['data']
    
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        engine = QueryEngine(user, database)
        
        record = Record(id=record_id, data=record_data)
        success = engine.insert(table_name, record)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Record {record_id} created successfully',
                'record': {'id': record_id, **record_data}
            }), 201
        else:
            return jsonify({'error': 'Failed to create record'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@record_bp.route('/<record_id>', methods=['GET'])
def get_record(user_id, db_name, table_name, record_id):
    """Get a specific record by ID"""
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        engine = QueryEngine(user, database)
        
        record = engine.find_by_id(table_name, record_id)
        
        if not record:
            return jsonify({'error': 'Record not found'}), 404
        
        return jsonify({
            'success': True,
            'record': {'id': record.id, **record.data}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@record_bp.route('/<record_id>', methods=['PUT'])
def update_record(user_id, db_name, table_name, record_id):
    """
    Update a record
    
    Request body:
        {
            "data": {}  // required
        }
    """
    data = request.get_json()
    
    if not data or 'data' not in data:
        return jsonify({'error': 'data is required'}), 400
    
    record_data = data['data']
    
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        engine = QueryEngine(user, database)
        
        record = Record(id=record_id, data=record_data)
        success = engine.update(table_name, record)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Record {record_id} updated successfully',
                'record': {'id': record_id, **record_data}
            })
        else:
            return jsonify({'error': 'Record not found or update failed'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@record_bp.route('/<record_id>', methods=['DELETE'])
def delete_record(user_id, db_name, table_name, record_id):
    """Delete a record"""
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        engine = QueryEngine(user, database)
        
        success = engine.delete(table_name, record_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Record {record_id} deleted successfully'
            })
        else:
            return jsonify({'error': 'Record not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
