"""Serialize account changes across the QQ Bot and Web worker."""

try:
    import fcntl
except ImportError:
    fcntl = None
    import msvcrt
from contextlib import contextmanager
from functools import wraps
from hashlib import sha256
from pathlib import Path
from threading import RLock, local

_registry_guard = RLock()
_locks: dict[str, RLock] = {}
_held = local()


@contextmanager
def account_lock(db_path: Path, user_id: str):
    key = f"{db_path.resolve()}:{user_id}"
    with _registry_guard:
        lock = _locks.setdefault(key, RLock())
    with lock:
        held = getattr(_held, "keys", set())
        if key in held:
            yield
            return
        directory = db_path.parent / ".account-locks"
        directory.mkdir(mode=0o700, exist_ok=True)
        path = directory / sha256(key.encode("utf-8")).hexdigest()
        with path.open("a+b") as handle:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            else:
                handle.seek(0, 2)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            _held.keys = held | {key}
            try:
                yield
            finally:
                _held.keys = held
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                else:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def serialized_user_action(method):
    @wraps(method)
    def wrapped(self, user_id, *args, **kwargs):
        with account_lock(
            getattr(self, "db_path", None) or self.repo.db_path, str(user_id)
        ):
            return method(self, user_id, *args, **kwargs)

    return wrapped
