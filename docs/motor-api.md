# Guia de uso da API do Motor de Prioridade

Este documento descreve como consumir os endpoints do motor de priorizacao de pagamentos.

## 1. Autenticacao

```http
Authorization: Bearer <seu_token>
Content-Type: application/json
```

Base URL:

```text
/api/motor/
```

## 2. O que e o Motor de Prioridade

O Motor de Prioridade analisa as despesas da firm para o mes atual e sugere uma ordem de pagamento com base no saldo disponivel em conta. Ele separa os pagamentos em dois grupos:

- **pagamentos_recomendados**: despesas que cabem no saldo disponivel.
- **pagamentos_nao_cobertos**: despesas que excedem o saldo.

O frontend pode reordenar esses cards e salvar a configuracao preferida.

## 3. Estrutura de dados

### SimulacaoPrioridade

```json
{
  "id": 1,
  "reference_period": "2026-06",
  "saldo_total_disponivel": "22400.00",
  "saldo_restante_pos_pagamentos": "5200.00",
  "created_at": "2026-06-04T10:00:00Z",
  "pagamentos_recomendados": [
    {
      "id": 10,
      "parcela": 55,
      "expense_title": "Aluguel do Escritorio",
      "category": "ESTRUTURA",
      "priority": "CRITICA",
      "due_date": "2026-06-10",
      "status_recomendacao": "RECOMENDADO",
      "amount_snapshot": "3500.00",
      "late_interest_snapshot": "0.00"
    }
  ],
  "pagamentos_nao_cobertos": [
    {
      "id": 11,
      "parcela": 60,
      "expense_title": "Software de Gestao",
      "category": "ESTRUTURA",
      "priority": "ALTA",
      "due_date": "2026-06-15",
      "status_recomendacao": "NAO_COBERTO",
      "amount_snapshot": "890.00",
      "late_interest_snapshot": "0.00"
    }
  ]
}
```

### Status de recomendacao

| Valor | Descricao |
|-------|-----------|
| `RECOMENDADO` | Pagamento cabe no saldo disponivel |
| `NAO_COBERTO` | Pagamento excede o saldo disponivel |

## 4. Calcular prioridades dinamicamente (GET)

```http
GET /api/motor/
```

Calcula e retorna a priorizacao para o mes atual sem salvar no banco.

Resposta `200`:

```json
{
  "reference_period": "2026-06",
  "saldo_total_disponivel": 22400.0,
  "saldo_restante_pos_pagamentos": 5200.0,
  "pagamentos_recomendados": [ ... ],
  "pagamentos_nao_cobertos": [ ... ]
}
```

Use este endpoint para renderizar os cards na tela na carga inicial.

## 5. Salvar configuracao personalizada (POST)

```http
POST /api/motor/salvar-configuracao/
```

Salva a ordem dos cards exatamente como o usuario deixou na tela.

```json
{
  "pagamentos_recomendados": [
    { "parcela": 60, "status_recomendacao": "RECOMENDADO", "amount_snapshot": "890.00", "late_interest_snapshot": "0.00" },
    { "parcela": 55, "status_recomendacao": "RECOMENDADO", "amount_snapshot": "3500.00", "late_interest_snapshot": "0.00" }
  ],
  "pagamentos_nao_cobertos": [
    { "parcela": 72, "status_recomendacao": "NAO_COBERTO", "amount_snapshot": "1200.00", "late_interest_snapshot": "15.00" }
  ]
}
```

Comportamento:
1. O backend preserva a ordem exata dos arrays enviados.
2. Cria ou sobrescreve a simulacao do mes atual para a firm.
3. Retorna o objeto salvo com ID e dados completos.

Resposta `201`:

```json
{
  "id": 1,
  "reference_period": "2026-06",
  "saldo_total_disponivel": "22400.00",
  "saldo_restante_pos_pagamentos": "5200.00",
  "pagamentos_recomendados": [ ... ],
  "pagamentos_nao_cobertos": [ ... ]
}
```

## 6. Checklist rapido para o frontend

1. Na carga da tela: `GET /api/motor/` para calcular dinamicamente.
2. Ao usuario confirmar a ordem dos cards: `POST /api/motor/salvar-configuracao/` com os dois arrays na ordem da tela.
3. A soma de `pagamentos_recomendados` + `pagamentos_nao_cobertos` no payload deve conter todos os cards.
4. O payload vazio retorna erro de validacao — sempre enviar pelo menos 1 item.
5. `amount_snapshot` e `late_interest_snapshot` devem ser os valores exibidos na tela (snapshot do momento).
