from ..entities import User, Database, Table, Record
from ..utils import sanitize_name
from .file_system import FileSystem
import os
from typing import Optional
from ..json_parser import JSONParser

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
        Uses sanitize_name to ensure filesystem-safe names.
        Respects NATURALDB_DATA_PATH environment variable for testing.
        """
        # Use environment variable if set, otherwise use local data directory
        base_dir = os.environ.get('NATURALDB_DATA_PATH', os.path.join(os.getcwd(), "data"))
        path = f"{base_dir}/{sanitize_name(user.id)}"
        if database:
            path += f"/{sanitize_name(database.name)}"
        if table:
            path += f"/{sanitize_name(table.name)}"
        if record:
            path += f"/{sanitize_name(record.id)}.json"
        return path

    def create_user(self, user: User) -> None:
        """
        Create a directory for the user.
        Uses FileSystem for thread-safe operations.
        """
        path = Storage.get_path(user)
        FileSystem.create_folder(path)
    
    def delete_user(self, user: User) -> None:
        """
        Delete the user's directory and all its contents.
        Uses FileSystem for thread-safe operations.
        """
        path = Storage.get_path(user)
        FileSystem.delete_folder(path)

    def create_database(self, user: User, database: Database) -> None:
        """
        Create a directory for the database.
        Uses FileSystem for thread-safe operations.
        """
        path = Storage.get_path(user, database)
        FileSystem.create_folder(path)
        metadata_path = f"{path}/metadata.json"
        metadata_content = JSONParser.to_json_string({'name': database.name, 'tables': []}, indent=2)
        FileSystem.create_file(metadata_path, metadata_content, recursive=False)
    
    def delete_database(self, user: User, database: Database) -> None:
        """
        Delete the database's directory and all its contents.
        Uses FileSystem for thread-safe operations.
        """
        path = Storage.get_path(user, database)
        FileSystem.delete_folder(path)

class DatabaseStorage:
    """
    The storage handler for a specific database.
    Manages tables within that database.
    
    """
    def __init__(self, user: User, database: Database) -> None:
        self.user = user
        self.database = database
        self.base_path = Storage.get_path(user, database)
        FileSystem.create_folder(self.base_path)
    
    @property
    def metadata(self) -> dict:
        """
        Load the database's metadata from a JSON file.
        Uses FileSystem for thread-safe operations.
        """
        metadata_path = f"{self.base_path}/metadata.json"
        content = FileSystem.read_file(metadata_path)
        if content is None:
            return {'name': self.database.name, 'tables': []}
        return JSONParser.parse_string(content)
    
    @metadata.setter
    def metadata(self, value: dict) -> None:
        """
        Save the database's metadata to a JSON file.
        Uses FileSystem for thread-safe operations.
        """
        metadata_path = f"{self.base_path}/metadata.json"
        content = JSONParser.to_json_string(value, indent=2)
        FileSystem.create_file(metadata_path, content, recursive=False)
        
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
        Uses FileSystem for thread-safe operations.
        """
        metadata_path = self.get_table_metadata_path(table)
        metadata_content = JSONParser.to_json_string({'name': table.name, 'keys': table.keys}, indent=2)
        FileSystem.create_file(metadata_path, metadata_content, recursive=False)
    
    def create_table(self, table: Table) -> None:
        """
        Create a directory for the table and save its metadata.
        Uses FileSystem for thread-safe operations.
        """
        path = self.get_table_path(table)
        FileSystem.create_folder(path)
        self.save_table_metadata(table)
    
    def delete_table(self, table: Table) -> None:
        """
        Delete the table's directory and all its contents.
        Uses FileSystem for thread-safe operations.
        """
        path = self.get_table_path(table)
        FileSystem.delete_folder(path)

    def __len__(self) -> int:
        """
        Get the number of tables in the database.
        """
        return len(self.metadata.get('tables', []))


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
        FileSystem.create_folder(self.base_path)

    @property
    def metadata(self) -> dict:
        """
        Load the table's metadata from a JSON file.
        Uses FileSystem for thread-safe operations.
        """
        metadata_path = f"{self.base_path}/metadata.json"
        content = FileSystem.read_file(metadata_path)
        if content is None:
            return {'name': self.table.name, 'indexes': {}}
        return JSONParser.parse_string(content)
        
    @metadata.setter
    def metadata(self, value: dict) -> None:
        """
        Save the table's metadata to a JSON file.
        Uses FileSystem for thread-safe operations.
        """
        metadata_path = f"{self.base_path}/metadata.json"
        content = JSONParser.to_json_string(value, indent=2)
        FileSystem.create_file(metadata_path, content, recursive=False)

    
    def get_record_path(self, record: Record) -> str:
        """
        Get the file path for a given record.
        """
        return f"{self.base_path}/{record.id}.json"
    
    def save_record(self, record: Record) -> None:
        """
        Save a record to a JSON file.
        Uses FileSystem for thread-safe operations.
        """
        record_path = self.get_record_path(record)
        content = JSONParser.to_json_string(record.data, indent=2)
        FileSystem.create_file(record_path, content, recursive=False)
    
    def load_record(self, record_id: str) -> Record:
        """
        Load a record from a JSON file.
        Uses FileSystem for thread-safe operations.
        """
        record_path = f"{self.base_path}/{sanitize_name(record_id)}.json"
        content = FileSystem.read_file(record_path)
        if content is None:
            raise FileNotFoundError(f"Record {record_id} not found")
        data = JSONParser.parse_string(content)
        return Record(id=record_id, data=data)
    
    def load_all_records(self) -> dict:
        """
        Load all records in the table.
        Uses FileSystem for thread-safe operations.
        """
        records = {}
        files = FileSystem.list_files(self.base_path, show_folder=False)
        for filename in files:
            if filename.endswith('.json') and filename != 'metadata.json':
                record_id = filename[:-5]  # Remove .json extension
                records[record_id] = self.load_record(record_id)
        return records

    def delete_record(self, record_id: str) -> None:
        """
        Delete a record's JSON file.
        Uses FileSystem for thread-safe operations.
        """
        record_path = f"{self.base_path}/{sanitize_name(record_id)}.json"
        FileSystem.delete_file(record_path)

    def list_records(self) -> list:
        """
        List all record IDs in the table.
        Uses FileSystem for thread-safe operations.
        """
        records = []
        files = FileSystem.list_files(self.base_path, show_folder=False)
        for filename in files:
            if filename.endswith('.json') and filename != 'metadata.json':
                records.append(filename[:-5])  # Remove .json extension
        return records
    
    def __len__(self) -> int:
        """
        Get the number of records in the table.
        """
        return len(self.list_records())
    

if __name__ == "__main__":
    # Example usage
    user = User(id="user1", name="Alice")
    database = Database(name="test_db")
    table = Table(name="test_table", indexes={})
    record = Record(id="record1", data={"field1": "value1", "field2": "value2"})

    storage = Storage()
    storage.create_user(user)
    storage.create_database(user, database)

    db_storage = DatabaseStorage(user, database)
    db_storage.create_table(table)

    table_storage = TableStorage(user, database, table)
    table_storage.save_record(record)

    loaded_record = table_storage.load_record("record1")
    print(loaded_record)

    print(f"Number of records in table: {len(table_storage)}")