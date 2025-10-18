from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class User:
    id: str
    name: str

@dataclass
class Database:
    name: str

@dataclass
class Index:
    name: str
    fields: List[str]

@dataclass
class Table:
    name: str
    indexes: Dict[str, Index]  # index name to Index object mapping
    keys: Optional[List[str]] = None  # Add keys field for backward compatibility

@dataclass
class Record:
    id: str
    data: Dict[str, Any]