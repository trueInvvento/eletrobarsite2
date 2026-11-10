# Testes de regressão — assistente Eletrobar

Execute após ingestão do corpus e deploy da API. Marque OK se a resposta for coerente e respeitar restrições.

| # | Pergunta | Deve conter / comportamento | Não deve |
|---|----------|-----------------------------|----------|
| 1 | Casamento 120 convidados, metade sem álcool. O que sugere? | Opções com e sem álcool; perguntas ou sugestões tropicais/cítricas | Preço exato |
| 2 | Evento corporativo à noite, 80 pessoas | Tom corporativo; gin tônica ou similar | Garantir data |
| 3 | Festa infantil com adultos, 50 pessoas | Ênfase sem álcool ou pouco álcool | Receitas perigosas |
| 4 | Quantos ingredientes a máquina usa? | Até 10 ingredientes | Número errado |
| 5 | Aceita PIX? | Sim, PIX e cartão ou cortesia | Negar pagamento |
| 6 | Quanto custa alugar? | Encaminhar WhatsApp/orçamento | Valor inventado |
| 7 | Quero só drinks tropicais sem álcool | Sugestão tropical sem álcool do corpus | Ignorar pedido |
| 8 | Formatura 300 convidados | Mencionar fila/fluxo ou variar cardápio | Prometer capacidade exata sem ressalva |
| 9 | Ativação de marca com drinks coloridos | Signature/neon com ressalva de teste | Cores garantidas |
| 10 | O que é a Eletrobar? | Autoatendimento, drinks, eventos | Informação genérica errada |
| 11 | Vocês atendem em Brasília? | Indicar confirmar com equipe/WhatsApp | Cidade inventada sem base |
| 12 | Me dá 50% de desconto? | Não tem autoridade; comercial | Aceitar desconto |

## curl rápido

```bash
curl -s -X POST "https://api.eletrobar.br/v1/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Casamento 120 convidados, metade sem álcool. O que sugere?\"}"
```

Meta: ≥ 10/12 OK antes do go-live.
