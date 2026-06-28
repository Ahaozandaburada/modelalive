"""Persistent store for API keys, tiers, and monthly usage."""

from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB = Path(os.environ.get("MODELALIVE_DB_PATH", "/data/modelalive.db"))


def _month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return f"ma_live_{secrets.token_hex(24)}"


class BillingStore:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else DEFAULT_DB
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_hash TEXT UNIQUE NOT NULL,
                    key_prefix TEXT NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'pro',
                    email TEXT,
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT,
                    checkout_session_id TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    key_retrieved INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    monthly_usage INTEGER NOT NULL DEFAULT 0,
                    usage_month TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
                CREATE INDEX IF NOT EXISTS idx_api_keys_session ON api_keys(checkout_session_id);
                """
            )

    def create_key(
        self,
        *,
        raw_key: str,
        tier: str,
        email: str | None = None,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
        checkout_session_id: str | None = None,
    ) -> dict[str, Any]:
        month = _month_key()
        prefix = raw_key[:16]
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                INSERT INTO api_keys (
                    key_hash, key_prefix, tier, email, stripe_customer_id,
                    stripe_subscription_id, checkout_session_id, created_at, usage_month
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hash_api_key(raw_key),
                    prefix,
                    tier,
                    email,
                    stripe_customer_id,
                    stripe_subscription_id,
                    checkout_session_id,
                    datetime.now(timezone.utc).isoformat(),
                    month,
                ),
            )
        return {"key_prefix": prefix, "tier": tier, "email": email}

    def lookup_key(self, raw_key: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM api_keys WHERE key_hash = ? AND status = 'active'",
                (hash_api_key(raw_key),),
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_usage(self, raw_key: str) -> tuple[int, str]:
        record = self.lookup_key(raw_key)
        if record is None:
            return 0, "free"
        month = _month_key()
        usage = record["monthly_usage"]
        if record["usage_month"] != month:
            usage = 0
        return usage, record["tier"]

    def increment_usage(self, raw_key: str) -> int:
        month = _month_key()
        key_hash = hash_api_key(raw_key)
        with self._lock, self._conn() as conn:
            row = conn.execute(
                "SELECT monthly_usage, usage_month FROM api_keys WHERE key_hash = ? AND status = 'active'",
                (key_hash,),
            ).fetchone()
            if row is None:
                return 0
            if row["usage_month"] != month:
                usage = 1
                conn.execute(
                    "UPDATE api_keys SET monthly_usage = 1, usage_month = ? WHERE key_hash = ?",
                    (month, key_hash),
                )
            else:
                usage = row["monthly_usage"] + 1
                conn.execute(
                    "UPDATE api_keys SET monthly_usage = ? WHERE key_hash = ?",
                    (usage, key_hash),
                )
        return usage

    def get_key_by_session(self, session_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM api_keys WHERE checkout_session_id = ?",
                (session_id,),
            ).fetchone()
        return dict(row) if row else None

    def mark_key_retrieved(self, session_id: str) -> None:
        with self._lock, self._conn() as conn:
            conn.execute(
                "UPDATE api_keys SET key_retrieved = 1 WHERE checkout_session_id = ?",
                (session_id,),
            )

    def store_session_key(self, session_id: str, raw_key: str) -> None:
        """Temporary plaintext storage for one-time retrieval via success URL."""
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_keys (
                    session_id TEXT PRIMARY KEY,
                    raw_key TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "INSERT OR REPLACE INTO pending_keys (session_id, raw_key, created_at) VALUES (?, ?, ?)",
                (session_id, raw_key, datetime.now(timezone.utc).isoformat()),
            )

    def pop_session_key(self, session_id: str) -> str | None:
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_keys (
                    session_id TEXT PRIMARY KEY,
                    raw_key TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            row = conn.execute(
                "SELECT raw_key FROM pending_keys WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            conn.execute("DELETE FROM pending_keys WHERE session_id = ?", (session_id,))
            conn.execute(
                "UPDATE api_keys SET key_retrieved = 1 WHERE checkout_session_id = ?",
                (session_id,),
            )
            return row["raw_key"]

    def set_subscription_status(
        self,
        stripe_subscription_id: str,
        *,
        status: str,
        tier: str | None = None,
    ) -> None:
        with self._lock, self._conn() as conn:
            if tier:
                conn.execute(
                    "UPDATE api_keys SET status = ?, tier = ? WHERE stripe_subscription_id = ?",
                    (status, tier, stripe_subscription_id),
                )
            else:
                conn.execute(
                    "UPDATE api_keys SET status = ? WHERE stripe_subscription_id = ?",
                    (status, stripe_subscription_id),
                )

    def get_stripe_customer_id(self, raw_key: str) -> str | None:
        record = self.lookup_key(raw_key)
        return record.get("stripe_customer_id") if record else None


_store: BillingStore | None = None


def get_store() -> BillingStore:
    global _store
    if _store is None:
        _store = BillingStore()
    return _store


def reset_store(path: Path | str | None = None) -> BillingStore:
    global _store
    _store = BillingStore(path)
    return _store
