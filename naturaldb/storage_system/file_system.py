import os
import shutil
from ..lock import lock_manager
from typing import Optional
from ..errors import NaturalDBError

class FileSystemError(NaturalDBError):
    """Custom exception for FileSystem errors"""
    def __init__(self, message: str):
        super().__init__(message, type="FileSystemError")

class FileSystem:
    """
    The file system for NaturalDB.
    
    """
    def __init__(self) -> None:
        pass

    @staticmethod
    def create_file(path: str, content: str, recursive: bool = True) -> None:
        """
        Create a file at the given path with the specified content.
        If recursive is True, create parent directories as needed.
        Otherwise, assume parent directories already exist.
        """
        lock_manager.acquire_write(path)
        try:
            if recursive:
                os.makedirs(os.path.dirname(path), exist_ok=True)
            elif not os.path.exists(os.path.dirname(path)):
                raise FileSystemError(f"Parent directory does not exist for path: {path}")
            with open(path, 'w') as f:
                f.write(content)
        finally:
            lock_manager.release_write(path)

    @staticmethod
    def read_file(path: str) -> Optional[str]:
        """
        Read the content of the file at the given path.
        """
        lock_manager.acquire_read(path)
        try:
            if not os.path.exists(path):
                return None
            with open(path, 'r') as f:
                return f.read()
        finally:
            lock_manager.release_read(path)

    @staticmethod
    def delete_file(path: str) -> None:
        """
        Delete the file at the given path.
        """
        lock_manager.acquire_write(path)
        try:
            if os.path.exists(path):
                os.remove(path)
        finally:
            lock_manager.release_write(path)

    @staticmethod
    def create_folder(path: str) -> None:
        """
        Create a folder at the given path.
        """
        lock_manager.acquire_write(path)
        try:
            os.makedirs(path, exist_ok=True)
        finally:
            lock_manager.release_write(path)
    
    @staticmethod
    def delete_folder(path: str) -> None:
        """
        Delete the folder at the given path and all its contents.
        """
        lock_manager.acquire_write(path)
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
        finally:
            lock_manager.release_write(path)

    @staticmethod
    def list_files(path: str, show_folder: bool = True) -> list:
        """
        List all files in the folder at the given path.
        """
        lock_manager.acquire_read(path)
        try:
            if not os.path.exists(path):
                return []
            if show_folder:
                return os.listdir(path)
            return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        finally:
            lock_manager.release_read(path)

