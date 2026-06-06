# Clients and Cases API Guide

This document explains how to consume the clients, cases (processes), and bulk import endpoints.

## Base URL and Authentication

- Base: `/api/cases/`
- All endpoints require JWT authentication.

Headers:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

## Available Endpoints

1. `GET /api/cases/clients/`
2. `POST /api/cases/clients/`
3. `GET /api/cases/clients/{id}/`
4. `PATCH /api/cases/clients/{id}/`
5. `DELETE /api/cases/clients/{id}/`
6. `POST /api/cases/clients/import/`
7. `GET /api/cases/processes/`
8. `POST /api/cases/processes/`
9. `GET /api/cases/processes/{id}/`
10. `PATCH /api/cases/processes/{id}/`
11. `DELETE /api/cases/processes/{id}/`

## Data Structures

### Client

```json
{
  "id": 1,
  "firm": 10,
  "name": "Maria da Silva",
  "email": "maria@test.com",
  "phone": "11999999999",
  "cpf_cnpj": "123.456.789-09",
  "type": "PF",
  "notes": "VIP client",
  "created_at": "2026-06-04T10:00:00Z"
}
```

### Process (Case)

```json
{
  "id": 10,
  "firm": 10,
  "client": 1,
  "client_details": {
    "id": 1,
    "name": "Maria da Silva"
  },
  "client_name": "Maria da Silva",
  "title": "Debt collection - Contract X",
  "status": "ATIVO",
  "total_fee": "15000.00",
  "payment_type": "INSTALLMENT",
  "win_probability": 0.7,
  "stage": "Initial",
  "expected_close_date": "2026-12-20",
  "schedules": [
    {
      "id": 100,
      "amount": "5000.00",
      "expected_date": "2026-08-10",
      "probability": 0.9,
      "paid": false
    }
  ],
  "created_at": "2026-06-04T10:00:00Z"
}
```

### Schedule (CasePaymentSchedule)

```json
{
  "id": 100,
  "amount": "5000.00",
  "expected_date": "2026-08-10",
  "probability": 0.9,
  "paid": false
}
```

## Accepted Enums

### Client type

- `PF`
- `PJ`

### Process status

- `ATIVO`
- `CONCLUIDO`

### Process payment_type

- `FIXED`
- `INSTALLMENT`
- `SUCCESS_FEE`
- `HYBRID`

## Clients CRUD

### List clients

```http
GET /api/cases/clients/
```

Behavior:

1. Returns only clients from authenticated user's firm.
2. Ordered by `name`.

### Create client

```http
POST /api/cases/clients/
```

```json
{
  "name": "Maria da Silva",
  "email": "maria@test.com",
  "phone": "11999999999",
  "cpf_cnpj": "123.456.789-09",
  "type": "PF",
  "notes": "VIP client"
}
```

`firm` is always assigned by backend.

### Retrieve, update, delete client

```http
GET /api/cases/clients/{id}/
PATCH /api/cases/clients/{id}/
DELETE /api/cases/clients/{id}/
```

## Processes CRUD

### List processes

```http
GET /api/cases/processes/
```

### Create process with schedules

```http
POST /api/cases/processes/
```

```json
{
  "client": 1,
  "title": "Debt collection - Contract X",
  "status": "ATIVO",
  "total_fee": "15000.00",
  "payment_type": "INSTALLMENT",
  "win_probability": 0.7,
  "stage": "Initial",
  "expected_close_date": "2026-12-20",
  "schedules": [
    { "amount": "5000.00", "expected_date": "2026-08-10", "probability": 0.9, "paid": false },
    { "amount": "10000.00", "expected_date": "2026-11-10", "probability": 0.7, "paid": false }
  ]
}
```

Rules:

1. `schedules` can be omitted.
2. `schedules` can be empty.
3. `client_name` is auto-filled from the selected client.
4. `firm` is assigned by backend.

### Retrieve, update, delete process

```http
GET /api/cases/processes/{id}/
PATCH /api/cases/processes/{id}/
DELETE /api/cases/processes/{id}/
```

## Bulk Import: Clients + Processes

### Endpoint

```http
POST /api/cases/clients/import/
```

### Expected payload

Array of clients with nested processes and schedules.

### Implemented rules

1. Payload must be an array.
2. Maximum 500 items per import.
3. Batch processing with partial result (`created` and `errors`).
4. Each client is processed in its own transaction.
5. If one client fails, nothing for that client is persisted.
6. `processes` can be empty or omitted.
7. `schedules` can be empty or omitted for each process.
8. Duplicate grouping inside payload:
   - by `cpf_cnpj` if provided;
   - otherwise by `email` if provided;
   - otherwise treated as independent client rows.
9. Database duplicates in same firm:
   - existing `cpf_cnpj` -> validation error;
   - existing `email` -> validation error.

### Error fields

1. `index`: 0-based index in original array.
2. `name`: client name from payload.
3. `detail`: validation or persistence error details.

## Frontend CSV Template Mapping

Template columns:

```text
nome, email, telefone, cpf_cnpj, tipo, observacoes,
caso_titulo, caso_status, caso_honorario, caso_pagamento,
caso_probabilidade, caso_fase, caso_data_encerramento,
parcela_1_valor, parcela_1_data, parcela_1_prob,
parcela_2_valor, parcela_2_data, parcela_2_prob
```

Mapping to JSON payload:

1. `nome` -> `name`
2. `email` -> `email`
3. `telefone` -> `phone`
4. `cpf_cnpj` -> `cpf_cnpj`
5. `tipo` -> `type`
6. `observacoes` -> `notes`
7. `caso_titulo` -> `processes[].title`
8. `caso_status` -> `processes[].status`
9. `caso_honorario` -> `processes[].total_fee`
10. `caso_pagamento` -> `processes[].payment_type`
11. `caso_probabilidade` -> `processes[].win_probability`
12. `caso_fase` -> `processes[].stage`
13. `caso_data_encerramento` -> `processes[].expected_close_date`
14. `parcela_n_valor/data/prob` -> `processes[].schedules[]`

## Frontend Checklist

1. Always send JWT.
2. For import, send an array payload.
3. Handle both `created` and `errors` in one response.
4. Show per-row feedback using `errors[index]`.
5. Expect backend grouping for repeated client rows.
