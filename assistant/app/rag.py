from typing import Any

from app.config import get_settings
from app.llm import embed_text


def search_chunks(conn, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
    settings = get_settings()
    k = top_k or settings.rag_top_k
    vector = embed_text(query)
    vector_literal = "[" + ",".join(str(x) for x in vector) + "]"

    rows = conn.execute(
        f"""
        SELECT c.content, c.metadata, d.title, d.source,
               1 - (c.embedding <=> %s::vector) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.embedding IS NOT NULL
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
        """,
        (vector_literal, vector_literal, k),
    ).fetchall()

    return [
        {
            "content": r["content"],
            "metadata": r["metadata"],
            "title": r["title"],
            "source": r["source"],
            "score": float(r["score"]) if r["score"] is not None else 0.0,
        }
        for r in rows
    ]


def format_context(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "(Nenhum trecho relevante encontrado na base de conhecimento.)"

    parts = []
    for i, ch in enumerate(chunks, start=1):
        title = ch.get("title") or ch.get("source") or "Fonte"
        parts.append(f"[{i}] {title}\n{ch['content']}")
    return "\n\n---\n\n".join(parts)
