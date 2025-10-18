from lock import lock_manager
import os


def read_file(path: str) -> str:
    """
    Read the content of a file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} does not exist.")
    lock_manager.acquire_read(path)
    try:
        with open(path, 'r') as f:
            return f.read()
    finally:
        lock_manager.release_read(path)

def write_file(path: str, content: str) -> None:
    """
    Write content to a file.
    """
    dir_path = os.path.dirname(path)
    os.makedirs(dir_path, exist_ok=True)
    lock_manager.acquire_write(path)
    try:
        with open(path, 'w') as f:
            f.write(content)
    finally:
        lock_manager.release_write(path)