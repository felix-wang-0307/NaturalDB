from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .utils import sanitize_name
from .logger import Logger
from .errors import NaturalDBError

_entity_logger = Logger(log_file="naturaldb_entities.log", to_console=False)
MAX_NAME_LENGTH = 80

class EntityError(NaturalDBError):
    """Custom exception for Entity errors"""
    def __init__(self, message: str):
        super().__init__(message, type="EntityError")

def _check_and_sanitize(label: str, value: str) -> str:
    if not isinstance(value, str):
        raise EntityError(f"{label} must be str, got {type(value).__name__}")
    s = sanitize_name(value)
    if s != value:
        # Either raise or assign sanitized; choose one. Here we assign sanitized.
        _entity_logger.log("WARNING", f"{label} sanitized from '{value}' to '{s}'")

    if len(s) > MAX_NAME_LENGTH:
        s = s[:MAX_NAME_LENGTH]
        _entity_logger.log("WARNING", f"{label} truncated to {MAX_NAME_LENGTH} characters")

    return s

def _check_list_strings(label: str, items: List[str]) -> List[str]:
    if not isinstance(items, list):
        raise EntityError(f"{label} must be a list of str")
    return [_check_and_sanitize(f"{label}[]", x) for x in items]

@dataclass
class User:
    id: str
    name: str

    def __post_init__(self):
        self.id = _check_and_sanitize("User.id", self.id)
        self.name = _check_and_sanitize("User.name", self.name)

@dataclass
class Database:
    name: str

    def __post_init__(self):
        self.name = _check_and_sanitize("Database.name", self.name)

@dataclass
class Index:
    name: str
    fields: List[str]

    def __post_init__(self):
        self.name = _check_and_sanitize("Index.name", self.name)
        self.fields = _check_list_strings("Index.fields", self.fields)

@dataclass
class Table:
    name: str
    indexes: Dict[str, 'Index']
    keys: Optional[List[str]] = None

    def __post_init__(self):
        self.name = _check_and_sanitize("Table.name", self.name)
        if not isinstance(self.indexes, dict):
            raise TypeError("Table.indexes must be dict[str, Index]")
        # Sanitize index keys and ensure embedded Index names sanitized already.
        new_indexes: Dict[str, Index] = {}
        for k, v in self.indexes.items():
            sk = _check_and_sanitize("Table.indexes key", k)
            if not isinstance(v, Index):
                raise TypeError("Table.indexes values must be Index instances")
            # v.__post_init__ already ran, but ensure its name key matches sanitized key if desired
            new_indexes[sk] = v
        self.indexes = new_indexes
        if self.keys is not None:
            self.keys = _check_list_strings("Table.keys", self.keys)

@dataclass
class Record:
    id: str
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.id = _check_and_sanitize("Record.id", self.id)
        if not isinstance(self.data, dict):
            raise TypeError("Record.data must be dict")