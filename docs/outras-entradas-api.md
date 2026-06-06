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
/api/other-income/
```

## 2. Regras importantes antes de integrar

1. Multi-tenant por firm: o backend sempre usa a firm do usuario autenticado.
2. O filtro de data e obrigatorio apenas na listagem (`GET /api/other-income/`). Endpoints de detalhe, atualizacao e delete nao exigem filtro.
3. Na listagem, envie apenas um tipo de filtro:
   - `year` + `month` juntos, ou
   - `start_date` + `end_date` juntos.
4. Para entradas parceladas:
   - as parcelas sao geradas automaticamente no `POST` do header;
   - status do header e controlado pelas parcelas;
   - nao altere status do header via `PATCH` para registro parcelado — altere cada parcela individualmente.
5. Se todas as parcelas ficarem `RECEBIDO`, o header vira `RECEBIDO` automaticamente.
6. Se qualquer parcela estiver `PENDENTE`, o header fica `PENDENTE`.
7. E possivel converter um registro de valor fixo para parcelado via `PATCH` (ver secao 5.2).
8. Alterar campos estruturais de um registro ja parcelado (`total_installments`, `installment_value`, `date`, `amount`) recria todas as parcelas.

## 3. Listar entradas (GET)

### 3.1 Filtro por mes/ano

```http
GET /api/other-income/?year=2026&month=6
```

### 3.2 Filtro por periodo

```http
GET /api/other-income/?start_date=2026-06-01&end_date=2026-06-30
```

### 3.3 Erros comuns no GET

- Sem filtros: retorna erro de validacao.
- Enviar apenas `year` sem `month` (ou vice-versa): erro de validacao.
- Enviar apenas `start_date` sem `end_date` (ou vice-versa): erro de validacao.
- Misturar `year/month` com `start_date/end_date`: erro de validacao.

## 4. Criar entrada (POST)

### 4.1 Entrada sem parcelamento

```http
POST /api/other-income/
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
POST /api/other-income/
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
PATCH /api/other-income/{id}/
```

### 5.1 Atualizar campos simples (nao parcelado)

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

Ao alterar `status` em registro nao parcelado, o backend sincroniza automaticamente a parcela unica.

### 5.2 Converter valor fixo para parcelado

Caso o advogado tenha criado como valor fixo e precise corrigir para parcelado:

```json
{
  "is_installment": true,
  "total_installments": 3,
  "installment_value": 500.00,
  "amount": 1500.00
}
```

Comportamento do backend:

1. Remove a parcela unica existente.
2. Gera as novas parcelas com base em `date`, `installment_value` e `total_installments`.
3. Forcca `status` do header para `PENDENTE`.

### 5.3 Alterar estrutura de registro ja parcelado

Alterar `total_installments`, `installment_value`, `date` ou `amount` em registro parcelado recria todas as parcelas.

```json
{
  "total_installments": 4,
  "installment_value": 750.00,
  "amount": 3000.00
}
```

Obs.: em registro parcelado, `status` deve ser alterado por parcela individualmente (ver secao 6).

## 6. Atualizar parcela individual (PATCH)

```http
PATCH /api/other-income/{id}/installments/{installment_id}/
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
DELETE /api/other-income/{id}/
```

Comportamento:

- Remove o header.
- Remove todas as parcelas relacionadas em cascata.
- Retorna `204 No Content`.

## 8. Importacao em lote (POST)

```http
POST /api/other-income/import/
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
2. Na listagem (`GET`), sempre enviar filtro valido (`year+month` ou `start_date+end_date`).
3. PATCH/GET por ID e DELETE nao precisam de filtro de data.
4. Para parcelado, atualizar status por installment endpoint — nao pelo header.
5. Para converter fixo em parcelado, enviar `is_installment: true` + campos estruturais no PATCH.
6. Tratar erros de validacao (400) por campo/mensagem.
7. No import, tratar simultaneamente `created` e `errors`.
