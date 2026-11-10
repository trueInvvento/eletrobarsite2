import json
from pathlib import Path
from uuid import UUID

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import (
    close_pool,
    db_conn,
    ensure_session,
    get_history,
    get_session_transcript,
    save_message,
)
from app.llm import chat_completion, embed_text
from app.rate_limit import check_rate_limit
from app.rag import format_context, search_chunks
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IngestDocument,
    LeadRequest,
    LeadResponse,
)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_system_prompt() -> str:
    path = PROMPTS_DIR / "system.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return "Você é o assistente da Eletrobar. Ajude com drinks para eventos usando apenas o contexto fornecido."


app = FastAPI(title="Eletrobar Assistant API", version="1.0.0")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
def _shutdown() -> None:
    close_pool()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    db_ok = False
    try:
        with db_conn() as conn:
            conn.execute("SELECT 1").fetchone()
            db_ok = True
    except Exception:
        db_ok = False
    status = "ok" if db_ok else "degraded"
    return HealthResponse(status=status, database=db_ok)


@app.post("/v1/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="Assistente indisponível (configuração).")

    check_rate_limit(request, bucket_suffix=str(payload.session_id or "new"))

    system = load_system_prompt()

    with db_conn() as conn:
        session_id = ensure_session(conn, payload.session_id, payload.visitor_id)
        save_message(conn, session_id, "user", payload.message.strip())

        chunks = search_chunks(conn, payload.message)
        context = format_context(chunks)
        history = get_history(conn, session_id, settings.chat_history_limit)

        augmented_system = (
            f"{system}\n\n"
            "## Contexto recuperado (use como fonte principal)\n"
            f"{context}\n"
        )

        messages = history.copy()
        if not messages or messages[-1]["content"] != payload.message.strip():
            messages.append({"role": "user", "content": payload.message.strip()})

        reply = chat_completion(augmented_system, messages)
        save_message(conn, session_id, "assistant", reply)

    return ChatResponse(session_id=session_id, reply=reply)


@app.post("/v1/lead", response_model=LeadResponse)
async def create_lead(payload: LeadRequest, request: Request) -> LeadResponse:
    if not settings.n8n_webhook_url:
        raise HTTPException(
            status_code=503,
            detail="Envio de orçamento temporariamente indisponível. Use o WhatsApp.",
        )

    check_rate_limit(request, bucket_suffix=f"lead:{payload.session_id}")

    with db_conn() as conn:
        transcript = get_session_transcript(conn, payload.session_id)
        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Sessão sem mensagens.")

        summary_prompt = [
            {
                "role": "user",
                "content": (
                    "Resuma em português, em até 8 linhas, o evento e as sugestões de drinks "
                    "discutidos nesta conversa. Não invente preços.\n\n"
                    f"{transcript}"
                ),
            }
        ]
        summary = chat_completion(
            "Você gera resumos objetivos para a equipe comercial da Eletrobar.",
            summary_prompt,
        )

        lead_payload = json.dumps(
            {"contact": payload.contact, "transcript_excerpt": transcript[:2000]}
        )
        conn.execute(
            """
            INSERT INTO leads (session_id, summary, payload)
            VALUES (%s, %s, %s::jsonb)
            """,
            (payload.session_id, summary, lead_payload),
        )
        conn.commit()  # lead row

    body = {
        "source": "assistant",
        "session_id": str(payload.session_id),
        "summary": summary,
        "contact": payload.contact,
        "transcript": transcript,
    }
    headers = {}
    if settings.n8n_webhook_secret:
        headers["X-Webhook-Secret"] = settings.n8n_webhook_secret

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(settings.n8n_webhook_url, json=body, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail="Falha ao encaminhar lead.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Falha ao encaminhar lead.") from exc

    return LeadResponse(
        ok=True,
        message="Resumo enviado! Nossa equipe entrará em contato em breve.",
    )


@app.post("/v1/ingest")
def ingest_doc(
    doc: IngestDocument,
    x_ingest_key: str | None = Header(None, alias="X-Ingest-Key"),
) -> dict:
    if not settings.ingest_api_key or x_ingest_key != settings.ingest_api_key:
        raise HTTPException(status_code=401, detail="Não autorizado.")

    import hashlib

    content_hash = hashlib.sha256(doc.content.encode("utf-8")).hexdigest()
    embedding = embed_text(doc.content)

    with db_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM documents WHERE source = %s AND content_hash = %s",
            (doc.source, content_hash),
        ).fetchone()
        if existing:
            return {"status": "skipped", "document_id": str(existing["id"])}

        meta_json = json.dumps(doc.metadata)
        row = conn.execute(
            """
            INSERT INTO documents (source, title, content_hash, metadata)
            VALUES (%s, %s, %s, %s::jsonb)
            RETURNING id
            """,
            (doc.source, doc.title, content_hash, meta_json),
        ).fetchone()
        doc_id = row["id"]

        vector_literal = "[" + ",".join(str(x) for x in embedding) + "]"
        conn.execute(
            """
            INSERT INTO chunks (document_id, content, embedding, chunk_index, metadata)
            VALUES (%s, %s, %s::vector, 0, %s::jsonb)
            """,
            (doc_id, doc.content, vector_literal, meta_json),
        )
        conn.commit()

    return {"status": "created", "document_id": str(doc_id)}
