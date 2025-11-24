#!/usr/bin/env python3
"""
Flask API Server for NaturalDB

Run this file to start the REST API server:
    python run_api.py

Or with custom host/port:
    python run_api.py --host 0.0.0.0 --port 8080
"""

import os
import argparse
from naturaldb.env_config import config
from naturaldb.api.app import create_app


def main():
    parser = argparse.ArgumentParser(description='Run NaturalDB REST API server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--base-path', help='Base path for data storage (default: ./data)')
    
    args = parser.parse_args()
    
    # Set base path if provided
    if args.base_path:
        os.environ['NATURALDB_BASE_PATH'] = args.base_path
        os.environ['NATURALDB_DATA_PATH'] = args.base_path
    
    # Create Flask app
    app = create_app()
    
    # Run server
    print(f"\n{'='*60}")
    print(f"🚀 NaturalDB REST API Server")
    print(f"{'='*60}")
    print(f"📍 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"💾 Data Path: {config.get_data_path()}")
    print(f"🐛 Debug Mode: {args.debug}")
    print(f"{'='*60}")
    print(f"\n📚 API Documentation:")
    print(f"  Health Check:  http://{args.host}:{args.port}/health")
    print(f"  API Info:      http://{args.host}:{args.port}/")
    print(f"  Users:         http://{args.host}:{args.port}/api/users")
    print(f"  Databases:     http://{args.host}:{args.port}/api/databases")
    print(f"{'='*60}\n")
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == '__main__':
    main()
