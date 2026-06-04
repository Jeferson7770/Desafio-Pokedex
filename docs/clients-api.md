# Guia Completo da API de Clients e Cases

Este documento descreve como consumir os endpoints de clientes, processos e importacao em lote.

## Base URL e autenticacao

- Base de clients/cases: `/api/cases/`
- Todos os endpoints exigem autenticacao JWT.

Headers:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

## Endpoints disponiveis

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

## Estrutura de dados

### Client

```json
{
  "id": 1,
  "firm": 10,
  "name": "Maria da Silva",
  "email": "maria@teste.com",
  "phone": "11999999999",
  "cpf_cnpj": "123.456.789-09",
  "type": "PF",
  "notes": "Cliente VIP",
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
    "name": "Maria da Silva",
    "email": "maria@teste.com",
    "phone": "11999999999",
    "cpf_cnpj": "123.456.789-09",
    "type": "PF",
    "notes": "Cliente VIP",
    "created_at": "2026-06-04T10:00:00Z"
  },
  "client_name": "Maria da Silva",
  "title": "Acao de Cobranca - Contrato X",
  "status": "ATIVO",
  "total_fee": "15000.00",
  "payment_type": "INSTALLMENT",
  "win_probability": 0.7,
  "stage": "Inicial",
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

## Enums aceitos

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

## CRUD de Clients

### Listar clientes

```http
GET /api/cases/clients/
```

Comportamento:

1. Retorna apenas clientes da firm do usuario autenticado.
2. Ordenacao por `name`.

### Criar cliente

```http
POST /api/cases/clients/
```

Body:

```json
{
  "name": "Maria da Silva",
  "email": "maria@teste.com",
  "phone": "11999999999",
  "cpf_cnpj": "123.456.789-09",
  "type": "PF",
  "notes": "Cliente VIP"
}
```

Comportamento:

- `firm` e sempre definida pelo backend a partir do usuario autenticado.

### Buscar, editar e remover cliente

```http
GET /api/cases/clients/{id}/
PATCH /api/cases/clients/{id}/
DELETE /api/cases/clients/{id}/
```

## CRUD de Processes

### Listar processos

```http
GET /api/cases/processes/
```

### Criar processo com schedules

```http
POST /api/cases/processes/
```

Body:

```json
{
  "client": 1,
  "title": "Acao de Cobranca - Contrato X",
  "status": "ATIVO",
  "total_fee": "15000.00",
  "payment_type": "INSTALLMENT",
  "win_probability": 0.7,
  "stage": "Inicial",
  "expected_close_date": "2026-12-20",
  "schedules": [
    { "amount": "5000.00", "expected_date": "2026-08-10", "probability": 0.9, "paid": false },
    { "amount": "10000.00", "expected_date": "2026-11-10", "probability": 0.7, "paid": false }
  ]
}
```

Regras:

1. `schedules` pode ser omitido.
2. `schedules` pode ser `[]`.
3. `client_name` e preenchido automaticamente com o nome do cliente.
4. `firm` e atribuida automaticamente pelo backend.

### Buscar, editar e remover processo

```http
GET /api/cases/processes/{id}/
PATCH /api/cases/processes/{id}/
DELETE /api/cases/processes/{id}/
```

## Importacao em lote de Clients + Processes

### Endpoint

```http
POST /api/cases/clients/import/
```

### Payload esperado

Array de clientes com processos e schedules aninhados:

```json
[
  {
    "name": "Maria da Silva",
    "email": "maria@teste.com",
    "phone": "11999999999",
    "cpf_cnpj": "123.456.789-09",
    "type": "PF",
    "notes": "Cliente VIP",
    "processes": [
      {
        "title": "Acao de Cobranca - Contrato X",
        "status": "ATIVO",
        "total_fee": "15000.00",
        "payment_type": "INSTALLMENT",
        "win_probability": 0.7,
        "stage": "Inicial",
        "expected_close_date": "2026-12-20",
        "schedules": [
          { "amount": "5000.00", "expected_date": "2026-08-10", "probability": 0.9, "paid": false },
          { "amount": "10000.00", "expected_date": "2026-11-10", "probability": 0.7, "paid": false }
        ]
      }
    ]
  }
]
```

### Regras implementadas

1. Payload deve ser array.
2. Limite maximo de 500 itens por importacao.
3. Processamento em lote com retorno parcial (`created` e `errors`).
4. Cada cliente e processado em transacao atomica.
5. Se um cliente falhar, nada desse cliente e persistido (incluindo processos/schedules).
6. `processes` pode ser vazio ou omitido.
7. `schedules` pode ser vazio ou omitido em cada processo.
8. Se o mesmo cliente aparecer em multiplas linhas do array, backend agrupa por:
   - `cpf_cnpj` quando informado;
   - senao `email` quando informado;
   - senao trata como cliente independente por linha.
9. Duplicidade em base por firm:
   - se `cpf_cnpj` ja existir, retorna erro;
   - se `email` ja existir, retorna erro.

### Resposta

```json
{
  "created": [
    {
      "id": 1,
      "firm": 10,
      "name": "Maria da Silva",
      "email": "maria@teste.com",
      "phone": "11999999999",
      "cpf_cnpj": "123.456.789-09",
      "type": "PF",
      "notes": "Cliente VIP",
      "created_at": "2026-06-04T10:00:00Z",
      "processes": [
        {
          "id": 10,
          "firm": 10,
          "client": 1,
          "client_name": "Maria da Silva",
          "title": "Acao de Cobranca - Contrato X",
          "status": "ATIVO",
          "total_fee": "15000.00",
          "payment_type": "INSTALLMENT",
          "win_probability": 0.7,
          "stage": "Inicial",
          "expected_close_date": "2026-12-20",
          "schedules": [
            { "id": 100, "amount": "5000.00", "expected_date": "2026-08-10", "probability": 0.9, "paid": false }
          ],
          "created_at": "2026-06-04T10:00:00Z"
        }
      ]
    }
  ],
  "errors": [
    { "index": 2, "name": "Joao Pereira", "detail": "CPF/CNPJ ja cadastrado" }
  ]
}
```

### Significado dos campos de erro

1. `index`: posicao do cliente no array original (base 0).
2. `name`: nome recebido no payload para facilitar log/UX.
3. `detail`: mensagem de validacao ou erro de persistencia.

## Template CSV do frontend e mapeamento

Template:

```text
nome, email, telefone, cpf_cnpj, tipo, observacoes,
caso_titulo, caso_status, caso_honorario, caso_pagamento,
caso_probabilidade, caso_fase, caso_data_encerramento,
parcela_1_valor, parcela_1_data, parcela_1_prob,
parcela_2_valor, parcela_2_data, parcela_2_prob
```

Mapeamento para payload JSON:

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

## Erros comuns e tratamento recomendado

1. `400 Payload deve ser um array de objetos.`
2. `400 Maximo de 500 registros por importacao.`
3. `400 O usuario nao possui nenhuma empresa vinculada...`
4. `errors[].detail` com erro de validacao de campos obrigatorios de client/process/schedule.
5. `errors[].detail` com duplicidade de CPF/CNPJ ou e-mail.

## Checklist para frontend

1. Sempre enviar JWT.
2. Enviar import em array.
3. Tratar `created` e `errors` no mesmo fluxo.
4. Mostrar feedback por `errors[index]`.
5. Considerar que linhas repetidas de um mesmo cliente podem ser agrupadas no backend.
