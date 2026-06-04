# Guia de uso da API de Outras Entradas

Este documento descreve como o frontend deve consumir os endpoints de Outras Entradas no backend.

## 1. Autenticacao

Todos os endpoints exigem token JWT no header:

```http
Authorization: Bearer <seu_token>
Content-Type: application/json
```

Base URL:

```text
/api/outras-entradas/
```

## 2. Regras importantes antes de integrar

1. Multi-tenant por firm: o backend sempre usa a firm do usuario autenticado.
2. GET exige filtro obrigatorio: voce deve enviar:
   - `year` + `month` juntos, ou
   - `start_date` + `end_date` juntos.
3. Nao pode misturar os dois tipos de filtro no mesmo GET.
4. Para entradas parceladas:
   - as parcelas sao geradas automaticamente no `POST` do header;
   - status do header e controlado pelas parcelas;
   - nao altere status do header via `PATCH` para registro parcelado;
   - altere cada parcela no endpoint de installment.
5. Se todas as parcelas ficarem `RECEBIDO`, o header vira `RECEBIDO` automaticamente.
6. Se qualquer parcela estiver `PENDENTE`, o header fica `PENDENTE`.

## 3. Listar entradas (GET)

### 3.1 Filtro por mes/ano

```http
GET /api/outras-entradas/?year=2026&month=6
```

### 3.2 Filtro por periodo

```http
GET /api/outras-entradas/?start_date=2026-06-01&end_date=2026-06-30
```

### 3.3 Erros comuns no GET

- Sem filtros: retorna erro de validacao.
- Enviar apenas `year` sem `month` (ou vice-versa): erro de validacao.
- Enviar apenas `start_date` sem `end_date` (ou vice-versa): erro de validacao.
- Misturar `year/month` com `start_date/end_date`: erro de validacao.

## 4. Criar entrada (POST)

### 4.1 Entrada sem parcelamento

```http
POST /api/outras-entradas/
```

Body:

```json
{
  "title": "Reembolso de custas",
  "amount": 1500.00,
  "date": "2026-06-10",
  "status": "PENDENTE",
  "notes": "",
  "is_installment": false,
  "total_installments": 1,
  "installment_value": 1500.00,
  "interest_rate_month": 0
}
```

### 4.2 Entrada parcelada

```http
POST /api/outras-entradas/
```

Body:

```json
{
  "title": "Consultoria externa",
  "amount": 9000.00,
  "date": "2026-06-01",
  "status": "PENDENTE",
  "notes": "",
  "is_installment": true,
  "total_installments": 3,
  "installment_value": 3000.00,
  "interest_rate_month": 1.5
}
```

Comportamento do backend:

1. Cria o header em Outras Entradas.
2. Gera 3 parcelas automaticamente com:
   - `installment_number`: 1, 2, 3
   - `amount`: 3000.00
   - `due_date`: 2026-06-01, 2026-07-01, 2026-08-01
   - `status`: `PENDENTE`

## 5. Atualizar header (PATCH)

```http
PATCH /api/outras-entradas/{id}/
```

Exemplo (nao parcelado):

```json
{
  "title": "Novo titulo",
  "amount": 1800.00,
  "date": "2026-06-15",
  "notes": "Atualizado",
  "installment_value": 1800.00,
  "interest_rate_month": 0
}
```

Observacoes:

1. Em registro parcelado, o backend bloqueia alteracao de estrutura de parcelamento (`is_installment`, `total_installments`, `installment_value`).
2. Em registro parcelado, `status` deve ser alterado por parcela, nao pelo header.
3. Editar header nao recria e nao altera parcelas existentes.

## 6. Atualizar parcela individual (PATCH)

```http
PATCH /api/outras-entradas/{id}/installments/{installment_id}/
```

### 6.1 Marcar como recebido

```json
{
  "status": "RECEBIDO",
  "paid_at": "2026-06-04T14:00:00Z"
}
```

### 6.2 Voltar para pendente

```json
{
  "status": "PENDENTE",
  "paid_at": null
}
```

Apos esse PATCH, o backend recalcula automaticamente o `status` do header.

## 7. Remover entrada (DELETE)

```http
DELETE /api/outras-entradas/{id}/
```

Comportamento:

- Remove o header.
- Remove todas as parcelas relacionadas em cascata.
- Retorna `204 No Content`.

## 8. Importacao em lote (POST)

```http
POST /api/outras-entradas/import/
```

Body esperado: array de objetos.

```json
[
  {
    "title": "Reembolso A",
    "amount": 1500.00,
    "date": "2026-06-10",
    "status": "PENDENTE",
    "notes": "",
    "is_installment": false,
    "total_installments": 1,
    "installment_value": 1500.00,
    "interest_rate_month": 0
  },
  {
    "title": "Consultoria B",
    "amount": 6000.00,
    "date": "2026-06-01",
    "status": "PENDENTE",
    "notes": "Projeto X",
    "is_installment": true,
    "total_installments": 2,
    "installment_value": 3000.00,
    "interest_rate_month": 0
  }
]
```

Resposta:

```json
{
  "created": [
    { "id": 1, "title": "Reembolso A" }
  ],
  "errors": [
    { "index": 1, "detail": "mensagem de erro" }
  ]
}
```

Comportamento:

1. Nunca aborta o lote inteiro por causa de 1 item invalido.
2. Processa item a item e separa `created` e `errors`.
3. Limite maximo: 500 itens por requisicao.

## 9. Checklist rapido para o frontend

1. Sempre enviar token no header.
2. No GET, sempre enviar filtro valido obrigatorio.
3. Para parcelado, atualizar status por installment endpoint.
4. Tratar erros de validacao (400) por campo/mensagem.
5. No import, tratar simultaneamente `created` e `errors`.
