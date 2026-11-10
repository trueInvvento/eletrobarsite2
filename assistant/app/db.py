from contextlib import contextmanager
from typing import Any, Iterator
from uuid import UUID

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import get_settings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=10,
            kwargs={"options": "-c search_path=eletrobar,public"},
        )
    return _pool


@contextmanager
def db_conn() -> Iterator[Any]:
    pool = get_pool()
    with pool.connection() as conn:
        conn.row_factory = dict_row
        yield conn


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def ensure_session(conn, session_id: UUID | None, visitor_id: str | None) -> UUID:
    if session_id:
        row = conn.execute(
            "SELECT id FROM chat_sessions WHERE id = %s",
            (session_id,),
        ).fetchone()
        if row:
            return row["id"]
        conn.execute(
            """
            INSERT INTO chat_sessions (id, visitor_id)
            VALUES (%s, %s)
            """,
            (session_id, visitor_id),
        )
        conn.commit()
        return session_id

    row = conn.execute(
        """
        INSERT INTO chat_sessions (visitor_id)
        VALUES (%s)
        RETURNING id
        """,
        (visitor_id,),
    ).fetchone()
    return row["id"]


def save_message(conn, session_id: UUID, role: str, content: str) -> None:
    conn.execute(
        """
        INSERT INTO chat_messages (session_id, role, content)
        VALUES (%s, %s, %s)
        """,
        (session_id, role, content),
    )
    conn.execute(
        "UPDATE chat_sessions SET updated_at = now() WHERE id = %s",
        (session_id,),
    )
    conn.commit()


def get_history(conn, session_id: UUID, limit: int) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        SELECT role, content FROM chat_messages
        WHERE session_id = %s AND role IN ('user', 'assistant')
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (session_id, limit),
    ).fetchall()
    rows.reverse()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def get_session_transcript(conn, session_id: UUID, limit: int = 40) -> str:
    rows = conn.execute(
        """
        SELECT role, content FROM chat_messages
        WHERE session_id = %s
        ORDER BY created_at ASC
        LIMIT %s
        """,
        (session_id, limit),
    ).fetchall()
    lines = []
    for r in rows:
        label = "Cliente" if r["role"] == "user" else "Assistente"
        lines.append(f"{label}: {r['content']}")
    return "\n".join(lines)
