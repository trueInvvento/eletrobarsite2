# Eletrobar — Site e Assistente RAG

Site estático (Vercel) + API FastAPI na VPS (Caddy, Postgres/pgvector, n8n).

## Site local

Abra `index.html` via servidor estático ou Vercel dev. O chat requer API configurada em `assets/config.js`.

## Assistente (API)

- Código: [`assistant/`](assistant/)
- Arquitetura: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Operação: [`docs/RUNBOOK.md`](docs/RUNBOOK.md)
- Testes: [`docs/TEST_PROMPTS.md`](docs/TEST_PROMPTS.md)
- n8n: [`docs/n8n-lead-workflow.md`](docs/n8n-lead-workflow.md)

## Primeiros passos na VPS

1. Aplicar `assistant/migrations/001_init.sql` no Postgres.
2. Configurar `assistant/.env` e subir container (`docker-compose.overlay.yml`).
3. `python assistant/scripts/ingest.py` com `DATABASE_URL` e `OPENAI_API_KEY`.
4. Configurar Caddy (`docs/deploy/Caddyfile.example`).
