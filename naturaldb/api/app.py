"""
Flask Application Factory
Creates and configures the NaturalDB REST API application
"""

from flask import Flask, jsonify
from flask_cors import CORS

# Register blueprints
from .controllers.database_controller import database_bp
from .controllers.table_controller import table_bp
from .controllers.record_controller import record_bp
from .controllers.query_controller import query_bp
from .controllers.user_controller import user_bp

def create_app(config=None):
    """
    Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Default configuration
    app.config.update({
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True,
    })
    
    # Update with custom config if provided
    if config:
        app.config.update(config)
    
    # Enable CORS for all routes
    CORS(app)
    
    app.register_blueprint(database_bp, url_prefix='/api/databases')
    app.register_blueprint(table_bp, url_prefix='/api/databases/<user_id>/<db_name>/tables')
    app.register_blueprint(record_bp, url_prefix='/api/databases/<user_id>/<db_name>/tables/<table_name>/records')
    app.register_blueprint(query_bp, url_prefix='/api/databases/<user_id>/<db_name>/query')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'NaturalDB API',
            'version': '1.0.0'
        })
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Welcome to NaturalDB REST API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'databases': '/api/databases',
                'tables': '/api/databases/{user_id}/{db_name}/tables',
                'records': '/api/databases/{user_id}/{db_name}/tables/{table_name}/records',
                'query': '/api/databases/{user_id}/{db_name}/query',
                'users': '/api/users'
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)