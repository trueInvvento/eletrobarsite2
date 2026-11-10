# Arquitetura — Eletrobar Site + Assistente RAG

## Visão

| Camada | Onde | Função |
|--------|------|--------|
| Site estático + chat UI | Vercel | `index.html`, assets, `chat.js` |
| TLS + proxy | VPS (Caddy) | `https://api.<dominio>` → API |
| API RAG | VPS (Docker) | FastAPI: chat, lead, ingest |
| Vetores + histórico | Postgres (pgvector) | Schema `eletrobar` |
| Rate limit | Redis | Contagem por IP/sessão |
| Leads | n8n (rede Docker) | Webhook interno |

## DNS (configuração manual)

| Registro | Destino |
|----------|---------|
| `www` / apex | Vercel (CNAME ou A conforme painel Vercel) |
| `api` | A → IP fixo Contabo |

Substitua `<dominio>` por seu domínio (ex.: `eletrobar.br`) em Caddy, `ALLOWED_ORIGINS` e [`assets/config.js`](../assets/config.js).

## Variáveis de ambiente (API — VPS)

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | Sim | Chat + embeddings |
| `DATABASE_URL` | Sim | `postgresql://user:pass@postgres:5432/db` (rede Docker) |
| `ALLOWED_ORIGINS` | Sim | URLs do site, separadas por vírgula |
| `OPENAI_CHAT_MODEL` | Não | Padrão: `gpt-4o-mini` |
| `OPENAI_EMBEDDING_MODEL` | Não | Padrão: `text-embedding-3-small` |
| `REDIS_URL` | Não | `redis://redis:6379/0` — rate limit |
| `RATE_LIMIT_PER_MINUTE` | Não | Padrão: `20` |
| `N8N_WEBHOOK_URL` | Para leads | Ex.: `http://n8n:5678/webhook/eletrobar-lead` |
| `N8N_WEBHOOK_SECRET` | Recomendado | Header `X-Webhook-Secret` |
| `INGEST_API_KEY` | Para ingestão | Header `X-Ingest-Key` em `POST /v1/ingest` |
| `RAG_TOP_K` | Não | Padrão: `5` |
| `CHAT_HISTORY_LIMIT` | Não | Padrão: `10` mensagens |

Nunca commitar `.env` com valores reais.

## Fluxo de chat

1. Browser → `POST https://api.<dominio>/v1/chat` com `session_id` e `message`.
2. API valida CORS, rate limit, persiste mensagem do usuário.
3. Embedding da pergunta → busca cosine em `eletrobar.chunks`.
4. Monta prompt (system + contexto + histórico) → OpenAI.
5. Persiste resposta do assistente → JSON `{ reply, session_id }`.

## Fluxo de lead

1. Browser → `POST /v1/lead` com `session_id` e opcional `contact`.
2. API resume conversa (LLM curto ou concatenação) e POST no webhook n8n.
3. n8n notifica comercial / planilha.

## Arquivos relevantes

- Migração: [`assistant/migrations/001_init.sql`](../assistant/migrations/001_init.sql)
- API: [`assistant/app/`](../assistant/app/)
- Deploy VPS: [`assistant/docker-compose.overlay.yml`](../assistant/docker-compose.overlay.yml), [`docs/deploy/Caddyfile.example`](deploy/Caddyfile.example)
- Corpus: [`assistant/data/`](../assistant/data/)
- Runbook: [`RUNBOOK.md`](RUNBOOK.md)
