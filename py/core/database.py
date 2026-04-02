"""Database connection and initialization for Super Agent Party."""

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import aiosqlite

from py.core.config import DATABASE_PATH, COVS_PATH

logger = logging.getLogger(__name__)

_db_init_done = False
_covs_db_init_done = False


async def init_db() -> None:
    """Initialize the main database with required tables."""
    global _db_init_done
    if _db_init_done:
        return

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at INTEGER,
                updated_at INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                data TEXT NOT NULL,
                created_at INTEGER,
                updated_at INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS plugin_registry (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT,
                enabled INTEGER DEFAULT 0,
                config TEXT,
                created_at INTEGER,
                updated_at INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS skill_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                parameters TEXT,
                result TEXT,
                error TEXT,
                started_at INTEGER,
                completed_at INTEGER
            )
        """)
        await db.commit()
        _db_init_done = True
        logger.info("Database initialized at %s", DATABASE_PATH)


async def init_covs_db() -> None:
    """Initialize the conversations database."""
    global _covs_db_init_done
    if _covs_db_init_done:
        return

    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(COVS_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
        await db.commit()
        _covs_db_init_done = True
        logger.info("Conversations database initialized at %s", COVS_PATH)


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """Get a database connection.

    Yields:
        aiosqlite.Connection: Database connection
    """
    await init_db()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


@asynccontextmanager
async def get_covs_db() -> AsyncIterator[aiosqlite.Connection]:
    """Get the conversations database connection.

    Yields:
        aiosqlite.Connection: Database connection
    """
    await init_covs_db()
    async with aiosqlite.connect(COVS_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def load_settings() -> Dict[str, Any]:
    """Load settings from database.

    Returns:
        Dictionary of settings
    """
    await init_db()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT data FROM settings WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return {}
            return {}


async def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to database.

    Args:
        settings: Settings dictionary to save
    """
    await init_db()
    data = json.dumps(settings, ensure_ascii=False, indent=2)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (id, data) VALUES (1, ?)",
            (data,)
        )
        await db.commit()


async def load_covs() -> Dict[str, Any]:
    """Load conversations from database.

    Returns:
        Dictionary with conversations
    """
    await init_covs_db()
    try:
        async with aiosqlite.connect(COVS_PATH) as db:
            async with db.execute("SELECT data FROM settings WHERE id = 1") as cursor:
                row = await cursor.fetchone()
                return json.loads(row[0]) if row else {"conversations": []}
    except Exception:
        return {"conversations": []}


async def save_covs(data: Dict[str, Any]) -> None:
    """Save conversations to database.

    Args:
        data: Conversations data to save
    """
    await init_covs_db()
    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    async with aiosqlite.connect(COVS_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (id, data) VALUES (1, ?)",
            (json_data,)
        )
        await db.commit()


async def record_skill_execution(
    skill_id: str,
    parameters: Dict[str, Any],
    result: Any = None,
    error: Optional[str] = None,
    started_at: Optional[int] = None,
    completed_at: Optional[int] = None,
) -> int:
    """Record a skill execution in the database.

    Args:
        skill_id: The skill identifier
        parameters: Execution parameters
        result: Execution result
        error: Error message if failed
        started_at: Start timestamp
        completed_at: Completion timestamp

    Returns:
        The row ID of the inserted record
    """
    import time
    await init_db()

    if started_at is None:
        started_at = int(time.time())
    if completed_at is None:
        completed_at = int(time.time())

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO skill_executions
            (skill_id, parameters, result, error, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                skill_id,
                json.dumps(parameters),
                json.dumps(result) if result is not None else None,
                error,
                started_at,
                completed_at,
            ),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_skill_executions(
    skill_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get skill execution history.

    Args:
        skill_id: Optional skill ID to filter by
        limit: Maximum number of records to return

    Returns:
        List of execution records
    """
    await init_db()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if skill_id:
            async with db.execute(
                """
                SELECT * FROM skill_executions
                WHERE skill_id = ?
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (skill_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute(
                """
                SELECT * FROM skill_executions
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()

        return [dict(row) for row in rows]
