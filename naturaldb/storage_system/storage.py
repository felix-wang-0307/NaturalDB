from entities import User, Database, Table, Record
from lock import lock_manager
import os
import shutil
import json
from typing import Optional

class Storage:
    """
    The storage system for NaturalDB.
    
    """
    def __init__(self) -> None:
        pass
    @staticmethod
    def get_path(user: User, database: Optional[Database] = None, table: Optional[Table] = None, record: Optional[Record] = None) -> str:
        """
        Get the file path for a given user, database, and optionally table and record.
        """
        path = f"/data/{user.id}"
        if database:
            path += f"/{database.name}"
        if table:
            path += f"/{table.name}"
        if record:
            path += f"/{record.id}.json"
        return path

    def create_user(self, user: User) -> None:
        """
        Create a directory for the user.
        """
        path = Storage.get_path(user)
        os.makedirs(path, exist_ok=True)
    
    def delete_user(self, user: User) -> None:
        """
        Delete the user's directory and all its contents.
        """
        path = Storage.get_path(user)
        if os.path.exists(path):
            shutil.rmtree(path)

    def create_database(self, user: User, database: Database) -> None:
        """
        Create a directory for the database.
        """
        path = Storage.get_path(user, database)
        os.makedirs(path, exist_ok=True)
        metadata_path = f"{path}/metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump({'name': database.name, 'tables': []}, f)
    
    def delete_database(self, user: User, database: Database) -> None:
        """
        Delete the database's directory and all its contents.
        """
        path = Storage.get_path(user, database)
        if os.path.exists(path):
            shutil.rmtree(path)

class DatabaseStorage:
    """
    The storage handler for a specific database.
    Manages tables within that database.
    
    """
    def __init__(self, user: User, database: Database) -> None:
        self.user = user
        self.database = database
        self.base_path = Storage.get_path(user, database)
        os.makedirs(self.base_path, exist_ok=True)
    
    @property
    def metadata(self) -> dict:
        """
        Load the database's metadata from a JSON file.
        """
        metadata_path = f"{self.base_path}/metadata.json"
        if not os.path.exists(metadata_path):
            return {'name': self.database.name, 'tables': []}
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    @metadata.setter
    def metadata(self, value: dict) -> None:
        """
        Save the database's metadata to a JSON file.
        """
        metadata_path = f"{self.base_path}/metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(value, f)
        
    def get_table_path(self, table: Table) -> str:
        """
        Get the file path for a given table.
        """
        return f"{self.base_path}/{table.name}"
    
    def get_table_metadata_path(self, table: Table) -> str:
        """
        Get the file path for a table's metadata.
        """
        return f"{self.get_table_path(table)}/metadata.json"
    
    def save_table_metadata(self, table: Table) -> None:
        """
        Save the table's metadata to a JSON file.
        """
        metadata_path = self.get_table_metadata_path(table)
        with open(metadata_path, 'w') as f:
            json.dump({'name': table.name, 'keys': table.keys}, f)
    
    def create_table(self, table: Table) -> None:
        """
        Create a directory for the table and save its metadata.
        """
        path = self.get_table_path(table)
        os.makedirs(path, exist_ok=True)
        self.save_table_metadata(table)


class TableStorage:
    """
    The storage handler for a specific table.
    Manages records within that table.
    
    """
    def __init__(self, user: User, database: Database, table: Table) -> None:
        self.user = user
        self.database = database
        self.table = table
        self.base_path = Storage.get_path(user, database, table)
        os.makedirs(self.base_path, exist_ok=True)

    @property
    def metadata(self) -> dict:
        """
        Load the table's metadata from a JSON file.
        """
        metadata_path = f"{self.base_path}/metadata.json"
        if not os.path.exists(metadata_path):
            return {'name': self.table.name, 'indexes': {}}
        with open(metadata_path, 'r') as f:
            return json.load(f)
        
    @metadata.setter
    def metadata(self, value: dict) -> None:
        """
        Save the table's metadata to a JSON file.
        """
        metadata_path = f"{self.base_path}/metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(value, f)

    
    def get_record_path(self, record: Record) -> str:
        """
        Get the file path for a given record.
        """
        return f"{self.base_path}/{record.id}.json"
    
    def save_record(self, record: Record) -> None:
        """
        Save a record to a JSON file.
        """
        record_path = self.get_record_path(record)
        with open(record_path, 'w') as f:
            json.dump(record.data, f)
    
    def load_record(self, record_id: str) -> Record:
        """
        Load a record from a JSON file.
        """
        record_path = f"{self.base_path}/{record_id}.json"
        with open(record_path, 'r') as f:
            data = json.load(f)
        return Record(id=record_id, data=data)
    
    def load_all_records(self) -> dict:
        """
        Load all records in the table.
        """
        records = {}
        for filename in os.listdir(self.base_path):
            if filename.endswith('.json') and filename != 'metadata.json':
                record_id = filename[:-5]  # Remove .json extension
                records[record_id] = self.load_record(record_id)
        return records

    def delete_record(self, record_id: str) -> None:
        """
        Delete a record's JSON file.
        """
        record_path = f"{self.base_path}/{record_id}.json"
        if os.path.exists(record_path):
            os.remove(record_path)

    def list_records(self) -> list:
        """
        List all record IDs in the table.
        """
        records = []
        for filename in os.listdir(self.base_path):
            if filename.endswith('.json') and filename != 'metadata.json':
                records.append(filename[:-5])  # Remove .json extension
        return records