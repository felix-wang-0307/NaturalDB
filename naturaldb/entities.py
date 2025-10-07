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
class Key:
    name: str
    fields: List[str]
    unique: bool = False

@dataclass
class Index:
    name: str
    fields: List[str]

@dataclass
class Table:
    name: str
    keys: Dict[str, Key]  # key name to Key object mapping
    indexes: Dict[str, Index]  # index name to Index object mapping

@dataclass
class Record:
    id: str
    data: Dict[str, Any]