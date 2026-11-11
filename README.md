# Eletrobar — Site e Assistente RAG

Site estático na **Vercel** (design v2 *Neon Liquid*) + API **FastAPI** na VPS (Caddy, Postgres/pgvector, n8n).

Referência completa do projeto: [`docs/REFERENCIA.md`](docs/REFERENCIA.md).

## Branches

| Branch | Uso |
|--------|-----|
| `master` | Produção do site na Vercel (`eletrobar.com.br`) |
| `redesign/v2-moderno` | Redesign v2 — hero, splash, imagens em `assets/v2/` |

## Substituir o site antigo pelo v2

O site novo **não** depende de build: a Vercel publica os arquivos estáticos da raiz (`vercel.json`).

1. **Commit** das alterações (site + docs + `assistant/prompts/system.txt` se for junto).
2. **Merge** de `redesign/v2-moderno` em `master` (PR no GitHub ou merge local).
3. **`git push origin master`** — a Vercel faz deploy automático se o projeto já aponta para `master`.
4. **Conferir** em produção: layout, imagens `assets/v2/`, chat, WhatsApp e preview mobile.
5. **Opcional:** branch de preview na Vercel antes do merge (`git push -u origin redesign/v2-moderno` e abrir o URL de preview).

Só push da branch de redesign **não** troca o site público enquanto a Vercel estiver configurada para publicar `master` (comportamento usual).

## Atualizar o assistente (VPS)

O prompt do modelo **não** sobe com o deploy da Vercel (`.vercelignore` exclui `assistant/`).

Depois de alterar `assistant/prompts/system.txt`:

1. Copiar o diretório `assistant/` para `~/stack/eletrobar-assistant` na VPS (ou `git pull` lá, se o servidor clona o mesmo repositório).
2. Recriar o container:

```bash
cd /home/wesle/stack
docker compose -f docker-compose.yml -f eletrobar-assistant/docker-compose.overlay.yml up -d --build eletrobar-api
```

3. Validar: `curl -s https://api.eletrobar.com.br/health` e um turno de chat no site.
4. Regressão: [`docs/TEST_PROMPTS.md`](docs/TEST_PROMPTS.md) (ajuste expectativas ao novo fluxo de cardápio, se necessário).

Alterações só no **corpus** (`assistant/data/*.md`) exigem ainda `python scripts/ingest.py` na VPS.

## Site local

Sirva a raiz com qualquer servidor estático (ou `vercel dev`). O chat exige `assets/config.js` com `window.ELETROBAR_API` apontando para a API e a origem local em `ALLOWED_ORIGINS`.

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
