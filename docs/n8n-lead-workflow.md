# n8n — Webhook de leads do assistente

## Objetivo

Receber resumos de conversas enviados por `POST /v1/lead` da API Eletrobar.

## Configuração no n8n

1. **Novo workflow** → nome: `Eletrobar — Lead Assistente`.
2. Nó **Webhook**:
   - Método: `POST`
   - Path: `eletrobar-lead` (URL interna: `http://n8n:5678/webhook/eletrobar-lead`)
   - Authentication: None (use validação por header no próximo nó).
3. Nó **IF** (opcional):
   - Condição: `{{ $json.headers["x-webhook-secret"] }}` igual a `{{ $env.N8N_ELETROBAR_SECRET }}`  
     ou comparar `{{ $json.body }}` após ajuste — na prática a API envia header `X-Webhook-Secret` no request HTTP; no Webhook n8n use **Header Auth** ou Code node:

```javascript
const expected = $env.N8N_ELETROBAR_SECRET;
const got = $input.first().json.headers?.['x-webhook-secret'];
if (expected && got !== expected) {
  throw new Error('Unauthorized');
}
return $input.all();
```

4. Nó **Set** — campos:
   - `session_id` → `{{ $json.body.session_id }}`
   - `summary` → `{{ $json.body.summary }}`
   - `contact` → `{{ $json.body.contact }}`
   - `source` → `{{ $json.body.source }}`

5. Ações (escolha uma ou mais):
   - **Gmail / SMTP** — assunto: `Lead Assistente Eletrobar — {{ $json.session_id }}`
   - **Google Sheets** — append row
   - **HTTP Request** — WhatsApp/Evolution se já integrado

6. **Publicar** o workflow (produção).

## Variáveis na API (`assistant/.env`)

```env
N8N_WEBHOOK_URL=http://n8n:5678/webhook/eletrobar-lead
N8N_WEBHOOK_SECRET=<mesmo valor do n8n>
```

A API só alcança n8n pela rede Docker; o site na Vercel chama apenas `https://api.<dominio>/v1/lead`.

## Payload de exemplo

```json
{
  "source": "assistant",
  "session_id": "uuid",
  "summary": "Resumo em texto...",
  "contact": null,
  "transcript": "Cliente: ...\nAssistente: ..."
}
```

## Teste manual

```bash
curl -X POST "http://127.0.0.1:5678/webhook-test/eletrobar-lead" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: SEU_SECRET" \
  -d '{"source":"assistant","session_id":"test","summary":"Teste"}'
```

Substitua `webhook-test` por `webhook` após publicar.
