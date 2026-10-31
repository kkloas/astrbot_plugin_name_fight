"""Browser-bound login challenges verified by trusted QQ group events."""

import secrets
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

CHALLENGE_TTL = 300
SESSION_TTL = 7 * 24 * 60 * 60
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


@dataclass(frozen=True)
class WebIdentity:
    user_id: str
    group_id: str
    display_name: str


def qq_group_identity(event) -> WebIdentity:
    if event.get_platform_name() != "aiocqhttp":
        raise ValueError("Please verify in a QQ group where this Bot is present.")
    user_id = str(event.get_sender_id())
    group_id = str(event.get_group_id())
    if not (user_id.isascii() and user_id.isdigit() and 5 <= len(user_id) <= 15):
        raise ValueError("The QQ sender identity is unavailable.")
    if not (group_id.isascii() and group_id.isdigit() and 5 <= len(group_id) <= 15):
        raise ValueError("Please send the verification command in a QQ group.")
    return WebIdentity(user_id, group_id, str(event.get_sender_name() or user_id)[:64])


def _hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


class AuthRateLimited(ValueError):
    pass


class WebAuthRepository:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS web_login_challenges (
                    device_hash TEXT PRIMARY KEY,
                    code_hash TEXT NOT NULL UNIQUE,
                    expires_at INTEGER NOT NULL,
                    user_id TEXT,
                    group_id TEXT,
                    display_name TEXT
                );
                CREATE TABLE IF NOT EXISTS web_login_sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    expires_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS web_auth_limits (
                    bucket TEXT PRIMARY KEY,
                    window_start INTEGER NOT NULL,
                    attempts INTEGER NOT NULL
                );
            """)

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=15)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def rate_limit(self, scope: str, subject: str, maximum: int, seconds: int = 60):
        now = int(time.time())
        bucket = _hash(f"{scope}:{subject}")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM web_auth_limits WHERE window_start < ?", (now - 3600,)
            )
            row = connection.execute(
                "SELECT * FROM web_auth_limits WHERE bucket = ?", (bucket,)
            ).fetchone()
            if row is None or now - row["window_start"] >= seconds:
                connection.execute(
                    "INSERT INTO web_auth_limits VALUES (?, ?, 1) "
                    "ON CONFLICT(bucket) DO UPDATE SET window_start = excluded.window_start, attempts = 1",
                    (bucket, now),
                )
            elif row["attempts"] >= maximum:
                raise AuthRateLimited("Too many attempts. Please wait a minute.")
            else:
                connection.execute(
                    "UPDATE web_auth_limits SET attempts = attempts + 1 WHERE bucket = ?",
                    (bucket,),
                )

    def create_challenge(
        self, previous_device: str | None = None
    ) -> tuple[str, str, int]:
        device = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + CHALLENGE_TTL
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM web_login_challenges WHERE expires_at <= ?",
                (int(time.time()),),
            )
            connection.execute(
                "DELETE FROM web_login_sessions WHERE expires_at <= ?",
                (int(time.time()),),
            )
            if previous_device:
                connection.execute(
                    "DELETE FROM web_login_challenges WHERE device_hash = ?",
                    (_hash(previous_device),),
                )
            for _ in range(5):
                code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
                try:
                    connection.execute(
                        "INSERT INTO web_login_challenges (device_hash, code_hash, expires_at) VALUES (?, ?, ?)",
                        (_hash(device), _hash(code), expires_at),
                    )
                    return device, code, expires_at
                except sqlite3.IntegrityError:
                    continue
        raise RuntimeError("Could not allocate a login challenge.")

    def confirm(self, code: str, identity: WebIdentity) -> None:
        self.rate_limit("qq-confirm", identity.user_id, 5)
        code = code.strip().upper()
        if len(code) != 8 or any(char not in CODE_ALPHABET for char in code):
            raise ValueError("Invalid or expired verification code.")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            result = connection.execute(
                "UPDATE web_login_challenges SET user_id = ?, group_id = ?, display_name = ? "
                "WHERE code_hash = ? AND expires_at > ? AND user_id IS NULL",
                (
                    identity.user_id,
                    identity.group_id,
                    identity.display_name,
                    _hash(code),
                    int(time.time()),
                ),
            )
            if result.rowcount != 1:
                raise ValueError("Invalid, expired, or already used verification code.")

    def exchange(self, device: str, previous_session: str | None = None) -> str | None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM web_login_challenges WHERE device_hash = ? AND expires_at > ?",
                (_hash(device), int(time.time())),
            ).fetchone()
            if row is None:
                raise ValueError("Verification expired. Please request a new code.")
            if row["user_id"] is None:
                return None
            token = secrets.token_urlsafe(32)
            connection.execute(
                "INSERT INTO web_login_sessions VALUES (?, ?, ?, ?, ?)",
                (
                    _hash(token),
                    row["user_id"],
                    row["group_id"],
                    row["display_name"],
                    int(time.time()) + SESSION_TTL,
                ),
            )
            connection.execute(
                "DELETE FROM web_login_challenges WHERE device_hash = ?",
                (_hash(device),),
            )
            if previous_session:
                connection.execute(
                    "DELETE FROM web_login_sessions WHERE token_hash = ?",
                    (_hash(previous_session),),
                )
            return token

    def get_identity(self, token: str | None) -> WebIdentity | None:
        if not token:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT user_id, group_id, display_name FROM web_login_sessions "
                "WHERE token_hash = ? AND expires_at > ?",
                (_hash(token), int(time.time())),
            ).fetchone()
        return WebIdentity(**dict(row)) if row else None

    def logout(self, token: str | None, device: str | None = None):
        with self._connect() as connection:
            if token:
                connection.execute(
                    "DELETE FROM web_login_sessions WHERE token_hash = ?",
                    (_hash(token),),
                )
            if device:
                connection.execute(
                    "DELETE FROM web_login_challenges WHERE device_hash = ?",
                    (_hash(device),),
                )
