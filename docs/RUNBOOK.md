# Runbook — Eletrobar Site + Assistente

## Deploy Vercel (site)

1. Conecte o repositório Git à Vercel.
2. Root directory: repositório raiz (`eletrobarsite2`).
3. Framework: Other / Static (`vercel.json` já define).
4. Domínio customizado (`www` + apex).
5. Ajuste [`assets/config.js`](../assets/config.js) com `https://api.<seu-dominio>`.
6. Adicione previews no `ALLOWED_ORIGINS` da API se testar branch preview: `https://*-seu-projeto.vercel.app`.

## Deploy API (VPS)

```bash
# No servidor
cd /home/wesle/stack
# Copiar assistant/ para eletrobar-assistant/
cp eletrobar-assistant/.env.example eletrobar-assistant/.env
# Editar .env

# Migração (uma vez)
docker compose exec postgres psql -U <user> -d <db> -f - < eletrobar-assistant/migrations/001_init.sql

# Subir API
docker compose -f docker-compose.yml -f eletrobar-assistant/docker-compose.overlay.yml up -d --build eletrobar-api
```

## Ingestão do corpus

Na VPS ou local com `DATABASE_URL` apontando ao Postgres:

```bash
cd eletrobar-assistant
export DATABASE_URL=...
export OPENAI_API_KEY=...
python scripts/ingest.py
```

Após ≥ 100 chunks, criar índice HNSW (SQL em `001_init.sql` comentado).

## Caddy

Ver [`deploy/Caddyfile.example`](deploy/Caddyfile.example). Recarregar: `sudo systemctl reload caddy`.

## Firewall (UFW) — referência

- `allow 22/tcp` (SSH restrito por IP se possível)
- `allow 80,443/tcp`
- **deny** 5432, 5678, 8080 públicos (8080 só em 127.0.0.1)

## Health e logs

```bash
curl -s https://api.eletrobar.br/health
docker compose logs eletrobar-api --tail 100
```

## Backup Postgres

```bash
docker compose exec postgres pg_dump -U <user> <db> -n eletrobar > backup-eletrobar-$(date +%F).sql
```

Restaurar: `psql ... -f backup.sql`

## Rollback API

```bash
docker compose pull # se usar tag fixa
git checkout <tag-anterior> -- eletrobar-assistant
docker compose ... up -d --build eletrobar-api
```

## Go-live checklist

- [ ] `GET /health` → `database: true`
- [ ] CORS com domínio de produção
- [ ] `scripts/ingest.py` executado
- [ ] [`TEST_PROMPTS.md`](TEST_PROMPTS.md) ≥ 10/12 OK
- [ ] n8n workflow publicado + teste `/v1/lead`
- [ ] `assets/config.js` com URL da API correta
- [ ] Rate limit Redis ativo (`REDIS_URL`)
- [ ] Monitoramento HTTP em `/health`

## Incidentes

| Sintoma | Ação |
|---------|------|
| 503 chat | Verificar `OPENAI_API_KEY` e quota OpenAI |
| 502 lead | n8n down ou URL errada; testar webhook |
| 429 | Rate limit; aguardar ou ajustar `RATE_LIMIT_PER_MINUTE` |
| CORS | Atualizar `ALLOWED_ORIGINS` e redeploy API |
