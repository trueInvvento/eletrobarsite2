# Referência do projeto — Eletrobar

Documento único do site estático e do assistente de drinks. Os procedimentos de deploy, incidentes e testes continuam nos arquivos citados no final; este texto descreve o que o sistema é, como as peças se conectam e onde cada comportamento está no código.

## O que é

A Eletrobar é uma máquina de drinks de autoatendimento para festas, casamentos, formaturas, eventos corporativos e ativações de marca. Marca da Invvento Tecnologia Ltda (CNPJ 44.046.047/0001-61).

O repositório entrega duas coisas:

1. **Site de uma página** publicado na Vercel: apresentação, canais de contato e o chat do assistente.
2. **API FastAPI** na VPS Contabo: responde o chat com busca em base própria (RAG), grava a conversa e encaminha um resumo de orçamento para o n8n.

O visitante nunca fala direto com a OpenAI, o Postgres ou o n8n. O browser só chama `https://api.eletrobar.com.br`.

## Canais públicos

| Canal | Valor |
|-------|--------|
| Site | `https://eletrobar.com.br` e `https://www.eletrobar.com.br` |
| API | `https://api.eletrobar.com.br` |
| WhatsApp | (61) 99370-3294 — `https://wa.me/5561993703294` |
| Instagram | [@eletrobar.br](https://www.instagram.com/eletrobar.br) |
| Telefone | `tel:+5561993703294` |

O número e o texto padrão do WhatsApp estão repetidos em `index.html` e em `assets/chat.js`. O prompt do assistente (`assistant/prompts/system.txt`) também cita o mesmo número.

## Mapa do repositório

```
eletrobarsite2/
├── index.html              # página única
├── styles.css              # visual do site
├── script.js               # menu, scroll e animações
├── vercel.json             # site estático na Vercel
├── .vercelignore           # não sobe assistant/, docs/ nem .playwright-mcp/
├── assets/
│   ├── config.js           # window.ELETROBAR_API
│   ├── chat.js             # widget do assistente
│   ├── v2/*.jpg            # imagens do redesign Neon Liquid (hero, serviços, splash)
│   ├── logo-splash.png     # logo / favicon
│   └── *.png               # material legado (não usado no HTML v2)
├── assistant/
│   ├── app/                # FastAPI
│   ├── data/               # corpus em Markdown
│   ├── prompts/system.txt  # regras do modelo
│   ├── scripts/ingest.py   # gera embeddings e grava no Postgres
│   ├── migrations/001_init.sql
│   ├── Dockerfile
│   ├── docker-compose.overlay.yml
│   ├── requirements.txt
│   └── .env.example
└── docs/
    ├── REFERENCIA.md       # este arquivo
    ├── ARCHITECTURE.md
    ├── RUNBOOK.md
    ├── TEST_PROMPTS.md
    ├── n8n-lead-workflow.md
    └── deploy/Caddyfile.example
```

`.gitignore` exclui `.env`, `assistant/.env`, `__pycache__`, `.venv` e `.vercel`. Segredos ficam só no `.env` da VPS.

## Como as peças se conectam

```
Visitante
   │
   ▼
Vercel  (index.html, styles.css, script.js, assets/)
   │  POST /v1/chat  e  POST /v1/lead
   ▼
Caddy na VPS  (TLS em api.eletrobar.com.br → 127.0.0.1:8080)
   │
   ▼
eletrobar-api  (container FastAPI)
   ├── OpenAI     chat (gpt-4o-mini) e embeddings (text-embedding-3-small)
   ├── Postgres   schema eletrobar, extensão pgvector
   ├── Redis      limite de requisições por IP e sessão
   └── n8n        webhook interno de lead (rede Docker, sem porta pública)
```

| Camada | Onde | Função |
|--------|------|--------|
| Site + chat | Vercel | HTML estático e widget |
| TLS e proxy | Caddy na VPS | `api.eletrobar.com.br` → porta 8080 local |
| API | Docker `eletrobar-api` | chat, lead, ingestão pontual, health |
| Vetores e histórico | Postgres (pgvector) | schema `eletrobar` |
| Rate limit | Redis | 20 requisições por minuto, por IP e sessão |
| Leads | n8n | webhook `eletrobar-lead` na rede Docker |

DNS: `www` e o apex apontam para a Vercel. O registro `api` é um A para o IP da Contabo.

## Site

Uma página em português (`lang="pt-BR"`), **redesign v2 “Neon Liquid”** (`redesign/v2-moderno`, merge em `master` para produção).

- **Tipografia:** Inter (corpo) e Space Grotesk (títulos), via Google Fonts; ícones Font Awesome 6.5.2 (CDN).
- **Visual:** fundo `#05060d`, texto `#f4f6fb`, destaque *lime* `#c8ff1f`, acentos rosa/violeta/ciano; gradiente em `.grad-text`. Largura máxima 1180px (`--max` em `styles.css`).
- **Fundo:** camada fixa `.site-bg` (radiais + grade pontilhada), sem imagem de fundo pesada.
- **Header:** barra fixa em formato “pill” (`.main-header`), logo textual EB + link “Solicitar orçamento” para WhatsApp.
- **Divisores:** ondas de splash reais (`assets/v2/splash-wave-*.jpg`) em blocos `.liquid`.
- **Meta/OG:** `theme-color` `#05060d`; `og:image` → `assets/v2/hero-bg.jpg`.

Seções, na ordem do HTML:

| Âncora | Conteúdo |
|--------|----------|
| `#topo` | Hero com foto `hero-bg.jpg`, stats (10 ingredientes, PIX, IA), chips flutuantes, CTAs |
| *(marquee)* | Faixa animada com tipos de evento (sem âncora) |
| `#sobre` | Máquina (`machine-hero.jpg`) e três feature cards |
| `#servicos` | Três cards com fotos `service-party/wedding/corporate.jpg` |
| `#funcionamento` | Processo visual + bullets (10 ingredientes, volume, PIX, reposição) |
| `#depoimentos` | Três depoimentos com avatares em `assets/v2/avatar-*.jpg` |
| `#assistente` | Painel de chat + botão “Enviar resumo para orçamento” |
| `#contato` | Card sobre `contact-bg.jpg` com canais WhatsApp, Instagram e telefone |

`script.js`: header `is-scrolled` após 24px, menu mobile, reveal (IntersectionObserver, limiar 0.12) e **scrollspy** (destaca o link da seção visível na nav).

Imagens v2 em uso: `assets/v2/hero-bg.jpg`, `machine-hero.jpg`, `splash-wave-1.jpg`, `splash-wave-2.jpg`, `service-*.jpg`, `process-pour.jpg`, `avatar-*.jpg`, `contact-bg.jpg`, mais `assets/logo-splash.png` no footer/favicon. PNGs antigos na raiz de `assets/` permanecem no repositório, mas o HTML v2 não os referencia.

Há também botão flutuante de WhatsApp (`.floating-whatsapp`) em todas as páginas.

### Publicar o v2 no lugar do site antigo

1. Merge de `redesign/v2-moderno` → `master` e `git push origin master`.
2. A Vercel publica a raiz sem build; confira domínios `eletrobar.com.br` / `www`.
3. O assistente na VPS é **independente** — ver seção [Assistente](#assistente) e [`README.md`](../README.md).

### Chat no browser

`assets/config.js` define `window.ELETROBAR_API` (hoje `https://api.eletrobar.com.br`). `assets/chat.js` só inicia se existir `#assistente` e essa URL.

- A sessão fica em `localStorage` na chave `eletrobar_chat_session_id`. Na primeira mensagem o browser gera um UUID e o envia; a API adota esse id.
- Envio: `POST /v1/chat` com `{ message, session_id }`. O campo aceita até 2000 caracteres no input (a API aceita até 4000).
- Orçamento: `POST /v1/lead` com `{ session_id }`. Depois do sucesso o botão some e aparece um link para o WhatsApp com o texto “Vim pelo assistente de drinks do site”.
- Erros da API (`detail`) aparecem como bolha do assistente. O texto da mensagem vai em `textContent`, então o HTML do usuário não é interpretado.

O HTML traz uma **mensagem inicial estática** no chat (convite genérico). A primeira resposta **real** do modelo segue `assistant/prompts/system.txt` (links do site/Instagram e pergunta sobre preferências de drinks).

O aviso de privacidade na seção diz que as conversas podem ser armazenadas e que preço e disponibilidade são confirmados pela equipe.

### Publicação do site (Vercel)

`vercel.json` trata o repositório como site estático (`outputDirectory: "."`, sem build, URLs limpas, sem barra final). A Vercel ignora `assistant/`, `docs/` e `.playwright-mcp/`.

Para ver localmente, sirva a raiz com qualquer servidor estático. O chat só responde se a API estiver no ar e o CORS incluir a origem local.

## Assistente

Papel definido em `assistant/prompts/system.txt`: **Assistente de Cardápio EletroBar** — sugere 10 ingredientes líquidos, 10 drinks (200 ml, percentuais), opcionalmente JSON de importação para o app, e encaminha orçamento via botão de lead ou WhatsApp. O modelo **não** persiste JSON no Postgres; persistência de conversa e leads usa as tabelas `chat_*` e `leads` + n8n.

O modelo não inventa a partir do treinamento. Cada pergunta passa por estas etapas em `POST /v1/chat` (`assistant/app/main.py`):

1. Recusa com 503 se `OPENAI_API_KEY` estiver vazia.
2. Aplica o rate limit (Redis). Sem `REDIS_URL`, o limite não é aplicado.
3. Garante a sessão e grava a mensagem do usuário.
4. Gera o embedding da pergunta e busca os 5 chunks mais próximos por cosseno (`RAG_TOP_K`).
5. Monta o prompt: `prompts/system.txt` + os trechos recuperados + as últimas 10 mensagens (`CHAT_HISTORY_LIMIT`).
6. Chama o chat com temperatura 0.4.
7. Grava a resposta e devolve `{ session_id, reply }`.

Se a busca não achar nada, o contexto vira a frase “Nenhum trecho relevante encontrado na base de conhecimento.” O prompt manda o modelo admitir que não sabe e indicar o WhatsApp. Ele também proíbe inventar preço, desconto, data ou cláusula, e proíbe mencionar RAG ou embeddings.

Fluxo conversacional resumido (detalhes no prompt):

1. Primeira resposta: links do site/Instagram + pergunta sobre preferências de bebidas (sem cardápio antes disso).
2. Depois das preferências: perfil, tabela de 10 ingredientes, tabela de 10 drinks, observações operacionais, oferta de salvar cardápio.
3. Com nome e telefone: JSON validado + orientação para **Enviar resumo para orçamento** ou WhatsApp (61) 99370-3294.

### Lead

`POST /v1/lead` exige sessão com mensagens. A API pede ao modelo um resumo de até 8 linhas (sem preços), grava em `leads` e faz POST no webhook do n8n com:

```json
{
  "source": "assistant",
  "session_id": "uuid",
  "summary": "texto",
  "contact": null,
  "transcript": "Cliente: ...\nAssistente: ..."
}
```

O header `X-Webhook-Secret` sai quando `N8N_WEBHOOK_SECRET` está definido. O campo `contact` existe no contrato, mas o widget do site ainda não o envia. Falha do n8n vira HTTP 502; webhook ausente vira 503 com orientação para usar o WhatsApp. O registro em `leads` é commitado antes do POST, então uma falha do n8n deixa o resumo no banco.

O passo a passo do workflow está em [`n8n-lead-workflow.md`](n8n-lead-workflow.md). Path de produção: `http://n8n:5678/webhook/eletrobar-lead`.

### Endpoints

| Método | Caminho | Auth | Resposta |
|--------|---------|------|----------|
| `GET` | `/health` | nenhuma | `{ status, database }` — `ok` ou `degraded` |
| `POST` | `/v1/chat` | CORS + rate limit | `{ session_id, reply }` |
| `POST` | `/v1/lead` | CORS + rate limit | `{ ok, message }` |
| `POST` | `/v1/ingest` | header `X-Ingest-Key` | `{ status, document_id }` |

CORS permite `GET`, `POST` e `OPTIONS`, sem credenciais, para as origens de `ALLOWED_ORIGINS`. A API escuta em `0.0.0.0:8080` dentro do container; o compose publica só `127.0.0.1:8080`.

`POST /v1/ingest` grava o corpo inteiro como um único chunk. O caminho normal de atualizar a base é `scripts/ingest.py`, que quebra o Markdown em pedaços.

### Módulos da API

| Arquivo | Papel |
|---------|--------|
| `app/main.py` | rotas, prompt, lead e ingestão pontual |
| `app/config.py` | variáveis de ambiente (`pydantic-settings`, arquivo `.env`) |
| `app/schemas.py` | contratos Pydantic |
| `app/db.py` | pool psycopg (1–10 conexões), `search_path=eletrobar,public` |
| `app/rag.py` | busca por `<=>` (distância de cosseno) e formatação do contexto |
| `app/llm.py` | embeddings e chat via SDK OpenAI |
| `app/rate_limit.py` | chave Redis `rl:chat:{ip}:{sufixo}`, janela de 60s, HTTP 429 |

O IP do rate limit vem de `X-Forwarded-For` (primeiro valor) ou do socket. Caddy preenche esse header com o cliente real.

Dependências fixadas em `assistant/requirements.txt`: FastAPI 0.115.6, Uvicorn 0.32.1, Pydantic 2.10.3, OpenAI 1.57.2, psycopg 3.2.3, httpx 0.28.1, redis 5.2.1. Imagem: `python:3.12-slim`.

### Variáveis de ambiente

Definidas em `assistant/.env` na VPS. Modelo em `assistant/.env.example`.

| Variável | Obrigatória | Padrão no código | Uso |
|----------|-------------|------------------|-----|
| `OPENAI_API_KEY` | sim | vazio (chat responde 503) | chat e embeddings |
| `DATABASE_URL` | sim | `postgresql://localhost/eletrobar` | pool da API e do script de ingestão |
| `ALLOWED_ORIGINS` | sim | `localhost:5500` e `127.0.0.1:5500` | CORS, origens separadas por vírgula |
| `OPENAI_CHAT_MODEL` | não | `gpt-4o-mini` | conclusão do chat e do resumo |
| `OPENAI_EMBEDDING_MODEL` | não | `text-embedding-3-small` | vetor de 1536 dimensões |
| `REDIS_URL` | não | vazio (sem limite) | `redis://redis:6379/0` na stack |
| `RATE_LIMIT_PER_MINUTE` | não | `20` | teto por janela de 60s |
| `N8N_WEBHOOK_URL` | para leads | vazio (lead responde 503) | URL interna do n8n |
| `N8N_WEBHOOK_SECRET` | recomendado | vazio | header `X-Webhook-Secret` |
| `INGEST_API_KEY` | para `POST /v1/ingest` | vazio (rota responde 401) | header `X-Ingest-Key` |
| `RAG_TOP_K` | não | `5` | trechos recuperados |
| `CHAT_HISTORY_LIMIT` | não | `10` | mensagens anteriores enviadas ao modelo |

Exemplo de origens de produção: `https://www.eletrobar.com.br,https://eletrobar.com.br`. Previews da Vercel precisam entrar nessa lista, senão o browser bloqueia o chat.

## Base de conhecimento

Arquivos em `assistant/data/`. Cada um abre com front matter (`title`, `source` e, quando existe, `tags`).

| Arquivo | `source` | Assunto |
|---------|----------|---------|
| `site-sobre.md` | `site-sobre` | o que é a máquina e para quais eventos |
| `servicos.md` | `servicos` | aluguel, particulares, corporativos |
| `funcionamento.md` | `funcionamento` | ingredientes, volume, pagamento, reposição |
| `cardapio.md` | `cardapio` | sugestões compatíveis com a mistura automática |
| `faq.md` | `faq` | convidados, sem álcool, pagamento, orçamento |
| `restricoes.md` | `restricoes` | o que o assistente não pode afirmar |

`scripts/ingest.py` lê esses `.md`, ignora o que já tem o mesmo hash do corpo e, para arquivo novo:

- quebra o texto em parágrafos, com pedaços de até 2400 caracteres e sobreposição de 200;
- gera embeddings em lote;
- grava `documents` e `chunks`.

```bash
cd assistant
# DATABASE_URL e OPENAI_API_KEY no ambiente
python scripts/ingest.py
python scripts/ingest.py --reindex   # apaga a source e reembute
```

`--reindex` apaga os documentos daquela `source` antes de inserir. Rode depois de editar o corpus. O índice HNSW em `001_init.sql` está comentado de propósito: crie-o quando houver pelo menos cerca de 100 chunks. Com poucos vetores a busca sequencial é suficiente.

Alterar o site não atualiza o assistente. Texto que o chat precisa conhecer tem de existir em `assistant/data/` e passar pela ingestão.

## Banco

Schema `eletrobar`, extensão `vector`. Migração: `assistant/migrations/001_init.sql`.

| Tabela | Guarda |
|--------|--------|
| `documents` | fonte, título, hash do conteúdo, metadata |
| `chunks` | texto, `embedding vector(1536)`, índice do pedaço |
| `chat_sessions` | id (pode ser o UUID do browser) e `visitor_id` |
| `chat_messages` | papel `user`, `assistant` ou `system`, e o texto |
| `leads` | resumo, payload JSON e sessão (fica nula se a sessão for apagada) |

`documents` tem índice único em `(source, content_hash)`. Apagar um documento apaga os chunks. A similaridade usada na busca é `1 - (embedding <=> vetor)`.

## Deploy da API

O overlay em `assistant/docker-compose.overlay.yml` entra no compose que já sobe Postgres, Redis e n8n em `/home/wesle/stack`. O serviço se chama `eletrobar-api`, reinicia sozinho, usa as redes `data` e `edge` e só sobe depois de Postgres e Redis saudáveis. O healthcheck interno chama `GET /health`.

Na VPS o diretório esperado é `~/stack/eletrobar-assistant` (cópia desta pasta `assistant/`).

```bash
cd /home/wesle/stack
cp eletrobar-assistant/.env.example eletrobar-assistant/.env
# editar .env

docker compose exec postgres psql -U <user> -d <db> -f - < eletrobar-assistant/migrations/001_init.sql

docker compose -f docker-compose.yml -f eletrobar-assistant/docker-compose.overlay.yml up -d --build eletrobar-api
```

Caddy (`docs/deploy/Caddyfile.example`) termina TLS em `api.eletrobar.com.br`, comprime com gzip, envia HSTS e `X-Content-Type-Options`, e faz proxy para `127.0.0.1:8080` com `X-Real-IP`, `X-Forwarded-For` e `X-Forwarded-Proto`. Recarregar com `sudo systemctl reload caddy`.

Portas públicas: 22, 80 e 443. Postgres (5432), n8n (5678) e a API (8080) não ficam expostos; 8080 escuta só em localhost.

## Operação

Checagem rápida:

```bash
curl -s https://api.eletrobar.com.br/health
docker compose logs eletrobar-api --tail 100
```

`database: true` confirma que o pool alcança o Postgres. Não confirma OpenAI, Redis nem n8n.

Backup do schema:

```bash
docker compose exec postgres pg_dump -U <user> <db> -n eletrobar > backup-eletrobar-$(date +%F).sql
```

| Sintoma | Onde olhar |
|---------|------------|
| 503 no chat | `OPENAI_API_KEY` vazia, chave inválida ou cota da OpenAI |
| 503 no lead | `N8N_WEBHOOK_URL` vazio; o visitante deve usar o WhatsApp |
| 502 no lead | n8n fora do ar, workflow não publicado ou URL errada |
| 429 | rate limit; esperar ou subir `RATE_LIMIT_PER_MINUTE` |
| CORS no browser | origem ausente em `ALLOWED_ORIGINS`; recriar o container depois de editar o `.env` |
| Resposta genérica ou “não sei” | corpus desatualizado ou ingestão não rodou |
| 401 em `/v1/ingest` | `X-Ingest-Key` diferente de `INGEST_API_KEY` |

Checklist de go-live, rollback e firewall estão em [`RUNBOOK.md`](RUNBOOK.md). Perguntas de regressão do assistente estão em [`TEST_PROMPTS.md`](TEST_PROMPTS.md): a meta é pelo menos 10 de 12 respostas corretas, sem preço inventado.

## O que mudar em cada tarefa

| Tarefa | Onde |
|--------|------|
| Texto, seção ou imagem do site | `index.html`, `styles.css`, `assets/v2/` (e `assets/` legado) |
| Publicar redesign v2 | merge `redesign/v2-moderno` → `master`, push; Vercel |
| Menu, scroll, animação de entrada | `script.js` |
| URL da API no browser | `assets/config.js` |
| Comportamento do chat e do botão de orçamento | `assets/chat.js` |
| Tom e limites do modelo | `assistant/prompts/system.txt` |
| Fatos que o assistente pode citar | `assistant/data/*.md` e depois `scripts/ingest.py` |
| Contrato ou rota nova | `assistant/app/schemas.py` e `main.py` |
| Tabela nova | nova migração em `assistant/migrations/` |
| Domínio da API ou headers de proxy | `docs/deploy/Caddyfile.example` e o Caddyfile real na VPS |
| Destino do lead | workflow n8n e `N8N_WEBHOOK_URL` |

## Documentos relacionados

| Arquivo | Quando usar |
|---------|-------------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | visão curta de camadas, DNS e fluxos |
| [`RUNBOOK.md`](RUNBOOK.md) | deploy, backup, rollback, incidentes, go-live |
| [`n8n-lead-workflow.md`](n8n-lead-workflow.md) | montar e testar o webhook de lead |
| [`TEST_PROMPTS.md`](TEST_PROMPTS.md) | regressão do assistente depois de ingerir ou publicar |
| [`../README.md`](../README.md) | entrada do repositório e primeiros passos |
