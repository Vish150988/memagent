"""Schema versioning and migrations for CrossAgentMemory backends."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import MemoryBackend

logger = logging.getLogger(__name__)

# Bump this whenever a new migration is added.
CURRENT_SCHEMA_VERSION = 2

_SQLITE_ENSURE_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL DEFAULT 0
)
"""

_POSTGRES_ENSURE_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL DEFAULT 0
)
"""


def _is_sqlite(backend: MemoryBackend) -> bool:
    from .sqlite import SQLiteBackend

    return isinstance(backend, SQLiteBackend)


def _execute_raw(backend: MemoryBackend, sql: str, params: tuple = ()) -> list:
    """Execute raw SQL against a backend and return rows."""
    if _is_sqlite(backend):
        conn = backend._connection()
        try:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            conn.commit()
            return rows
        finally:
            backend._close(conn)
    else:
        conn = backend._connection()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            # Only fetch rows for SELECT-like statements
            rows = cur.fetchall() if cur.description else []
            conn.commit()
            return rows


def ensure_version_table(backend: MemoryBackend) -> None:
    """Create the schema_version tracking table if it doesn't exist."""
    if _is_sqlite(backend):
        _execute_raw(backend, _SQLITE_ENSURE_VERSION_TABLE)
    else:
        _execute_raw(backend, _POSTGRES_ENSURE_VERSION_TABLE)


def get_schema_version(backend: MemoryBackend) -> int:
    """Return the current schema version, or 0 if never initialized."""
    try:
        rows = _execute_raw(backend, "SELECT version FROM schema_version WHERE id = 1")
        if rows:
            return rows[0][0]
    except Exception:
        pass
    return 0


def set_schema_version(backend: MemoryBackend, version: int) -> None:
    """Persist the schema version."""
    if _is_sqlite(backend):
        _execute_raw(
            backend,
            """
            INSERT INTO schema_version (id, version) VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET version = excluded.version
            """,
            (version,),
        )
    else:
        _execute_raw(
            backend,
            """
            INSERT INTO schema_version (id, version) VALUES (1, %s)
            ON CONFLICT(id) DO UPDATE SET version = EXCLUDED.version
            """,
            (version,),
        )


MIGRATIONS = [
    # (version, description, sqlite_sql, postgres_sql)
    (
        2,
        "Add user_id, tenant_id, valid_from, valid_until to memories",
        """
        ALTER TABLE memories ADD COLUMN user_id TEXT NOT NULL DEFAULT '';
        ALTER TABLE memories ADD COLUMN tenant_id TEXT NOT NULL DEFAULT '';
        ALTER TABLE memories ADD COLUMN valid_from TEXT NOT NULL DEFAULT '';
        ALTER TABLE memories ADD COLUMN valid_until TEXT NOT NULL DEFAULT '';
        CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id);
        CREATE INDEX IF NOT EXISTS idx_memories_tenant ON memories(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_memories_valid_from ON memories(valid_from);
        CREATE INDEX IF NOT EXISTS idx_memories_valid_until ON memories(valid_until);
        """,
        """
        ALTER TABLE memories ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT '';
        ALTER TABLE memories ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT '';
        ALTER TABLE memories ADD COLUMN IF NOT EXISTS valid_from TIMESTAMPTZ;
        ALTER TABLE memories ADD COLUMN IF NOT EXISTS valid_until TIMESTAMPTZ;
        CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id);
        CREATE INDEX IF NOT EXISTS idx_memories_tenant ON memories(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_memories_valid_from ON memories(valid_from);
        CREATE INDEX IF NOT EXISTS idx_memories_valid_until ON memories(valid_until);
        """,
    ),
]


def run_migrations(backend: MemoryBackend) -> None:
    """Apply any pending schema migrations."""
    ensure_version_table(backend)
    current = get_schema_version(backend)

    if current >= CURRENT_SCHEMA_VERSION:
        return

    logger.info(
        "Migrating %s schema from version %d to %d",
        backend.__class__.__name__,
        current,
        CURRENT_SCHEMA_VERSION,
    )

    for version, description, sqlite_sql, postgres_sql in MIGRATIONS:
        if version <= current:
            continue
        logger.info("Running migration %d: %s", version, description)
        sql = sqlite_sql if _is_sqlite(backend) else postgres_sql
        # Split and execute each statement
        for stmt in sql.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    _execute_raw(backend, stmt)
                except Exception as exc:
                    logger.warning("Migration statement skipped: %s (%s)", stmt, exc)
        current = version

    set_schema_version(backend, CURRENT_SCHEMA_VERSION)
