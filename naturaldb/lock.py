import threading
from collections import defaultdict

class RWLock:
    """A Read-Write lock allowing multiple readers or one writer."""
    def __init__(self):
        self._readers = 0
        self._writer = False
        self._cond = threading.Condition()

    def acquire_read(self):
        with self._cond:
            while self._writer:
                self._cond.wait()
            self._readers += 1

    def release_read(self):
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    def acquire_write(self):
        with self._cond:
            while self._writer or self._readers > 0:
                self._cond.wait()
            self._writer = True

    def release_write(self):
        with self._cond:
            self._writer = False
            self._cond.notify_all()


class LockManager:
    """Manages RW locks per file path."""
    def __init__(self):
        self._locks = defaultdict(RWLock)
        self._global_lock = threading.Lock()

    def get_lock(self, path: str) -> RWLock:
        with self._global_lock:
            return self._locks[path]

    # ---- Public API ----
    def acquire_read(self, path: str):
        lock = self.get_lock(path)
        lock.acquire_read()

    def release_read(self, path: str):
        lock = self.get_lock(path)
        lock.release_read()

    def acquire_write(self, path: str):
        lock = self.get_lock(path)
        lock.acquire_write()

    def release_write(self, path: str):
        lock = self.get_lock(path)
        lock.release_write()

# Singleton instance
lock_manager = LockManager()