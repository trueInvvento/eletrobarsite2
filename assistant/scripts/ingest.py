#!/usr/bin/env python3
"""
Ingere arquivos .md de assistant/data/ no Postgres (schema eletrobar).

Uso (na pasta assistant/):
  set OPENAI_API_KEY=...
  set DATABASE_URL=postgresql://...
  python scripts/ingest.py
  python scripts/ingest.py --reindex   # ignora hash e re-embedding (cuidado)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

sys.path.insert(0, str(ROOT))

from psycopg.rows import dict_row  # noqa: E402
from psycopg_pool import ConnectionPool  # noqa: E402

from app.llm import embed_batch  # noqa: E402


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        return {}, text.strip()
    meta_lines = match.group(1)
    body = match.group(2).strip()
    metadata: dict = {}
    for line in meta_lines.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            metadata[key] = [v.strip() for v in inner.split(",") if v.strip()]
        elif val.lower() in ("true", "false"):
            metadata[key] = val.lower() == "true"
        else:
            metadata[key] = val
    return metadata, body


def chunk_text(text: str, max_chars: int = 2400, overlap: int = 200) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            if len(para) <= max_chars:
                current = para
            else:
                start = 0
                while start < len(para):
                    end = start + max_chars
                    chunks.append(para[start:end])
                    start = end - overlap
                current = ""
    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reindex", action="store_true")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL obrigatório", file=sys.stderr)
        sys.exit(1)
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY obrigatório", file=sys.stderr)
        sys.exit(1)

    pool = ConnectionPool(
        conninfo=database_url,
        kwargs={"options": "-c search_path=eletrobar,public"},
    )

    files = sorted(DATA_DIR.glob("*.md"))
    if not files:
        print(f"Nenhum .md em {DATA_DIR}")
        sys.exit(1)

    for path in files:
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        source = str(meta.get("source") or path.stem)
        title = str(meta.get("title") or path.stem)
        doc_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        meta_json = json.dumps(meta)

        with pool.connection() as conn:
            conn.row_factory = dict_row
            if not args.reindex:
                existing = conn.execute(
                    "SELECT id FROM documents WHERE source = %s AND content_hash = %s",
                    (source, doc_hash),
                ).fetchone()
                if existing:
                    print(f"skip {source} (unchanged)")
                    continue

            if args.reindex:
                conn.execute("DELETE FROM documents WHERE source = %s", (source,))

            row = conn.execute(
                """
                INSERT INTO documents (source, title, content_hash, metadata)
                VALUES (%s, %s, %s, %s::jsonb)
                RETURNING id
                """,
                (source, title, doc_hash, meta_json),
            ).fetchone()
            doc_id = row["id"]

            pieces = chunk_text(body)
            vectors = embed_batch(pieces)

            for idx, (piece, vector) in enumerate(zip(pieces, vectors, strict=True)):
                vector_literal = "[" + ",".join(str(x) for x in vector) + "]"
                conn.execute(
                    """
                    INSERT INTO chunks (document_id, content, embedding, chunk_index, metadata)
                    VALUES (%s, %s, %s::vector, %s, %s::jsonb)
                    """,
                    (doc_id, piece, vector_literal, idx, meta_json),
                )
            conn.commit()
            print(f"ingested {source} ({len(pieces)} chunks)")

    pool.close()
    print("done")


if __name__ == "__main__":
    main()
