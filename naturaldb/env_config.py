"""
Environment Configuration Module
Handles loading and managing environment variables for NaturalDB
"""

import os
from pathlib import Path
from typing import Optional


class EnvConfig:
    """Environment configuration manager for NaturalDB"""
    
    _instance = None
    _loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._loaded:
            self.load_env()
            EnvConfig._loaded = True
    
    @staticmethod
    def load_env(env_file: Optional[str] = None) -> None:
        """
        Load environment variables from .env file
        
        Args:
            env_file: Path to .env file. If None, searches in naturaldb directory
        """
        env_path: Path
        if env_file is None:
            # Try to find .env in naturaldb directory
            current_file = Path(__file__).resolve()
            naturaldb_dir = current_file.parent
            env_path = naturaldb_dir / '.env'
            
            # If not found, try parent directory
            if not env_path.exists():
                env_path = naturaldb_dir.parent / '.env'
        else:
            env_path = Path(env_file)
        
        if not env_path.exists():
            # No .env file found, use defaults
            return
        
        # Read and parse .env file
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Only set if not already in environment
                    # (existing env vars take precedence)
                    if key not in os.environ:
                        os.environ[key] = value
    
    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)
    
    @staticmethod
    def get_data_path() -> str:
        """Get the data storage path"""
        return os.getenv('NATURALDB_DATA_PATH', './data')
    
    @staticmethod
    def get_base_path() -> str:
        """Get the base path (legacy)"""
        return os.getenv('NATURALDB_BASE_PATH', './data')
    
    @staticmethod
    def get_openai_api_key() -> Optional[str]:
        """Get OpenAI API key"""
        return os.getenv('OPENAI_API_KEY')
    
    @staticmethod
    def get_flask_config() -> dict:
        """Get Flask configuration"""
        return {
            'ENV': os.getenv('FLASK_ENV', 'development'),
            'DEBUG': os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
            'HOST': os.getenv('FLASK_HOST', '127.0.0.1'),
            'PORT': int(os.getenv('FLASK_PORT', '5000'))
        }
    
    @staticmethod
    def get_log_level() -> str:
        """Get logging level"""
        return os.getenv('LOG_LEVEL', 'INFO')


# Initialize config on import
config = EnvConfig()
