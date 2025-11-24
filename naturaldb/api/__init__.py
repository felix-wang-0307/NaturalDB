"""
NaturalDB RESTful API
Provides HTTP interface for database operations similar to Firebase/MongoDB
"""

from .app import create_app
from .controllers import *

__all__ = ['create_app']
