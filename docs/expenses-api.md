# Guia Completo da API de Expenses

Este documento descreve como usar os endpoints de expenses no backend atual.

## Base URL e autenticacao

- Base: `/api/expenses/`
- Todos os endpoints exigem JWT:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

## Visao geral dos endpoints

1. `GET /api/expenses/`
2. `POST /api/expenses/`
3. `GET /api/expenses/{id}/`
4. `PATCH /api/expenses/{id}/`
5. `DELETE /api/expenses/{id}/`
6. `POST /api/expenses/import/`
7. `POST /api/expenses/defer-installment/{installment_id}/`
8. `GET /api/expenses/yearly-summary/`

## Estrutura de dados

### Expense

```json
{
  "id": 1,
  "firm": 10,
  "title": "Aluguel da Sala",
  "description": "Contrato anual",
  "amount": "4800.00",
  "due_date": "2026-10-10",
  "frequency": "ONE_TIME",
  "category": "ESTRUTURA",
  "category_display": "Estrutura",
  "priority": "LEGAL",
  "priority_display": "Legal / Critico",
  "is_paid": false,
  "paid_at": null,
  "is_active": true,
  "is_installment": false,
  "total_installments": 1,
  "installment_value": 4800.0,
  "interest_rate_month": "0.00",
  "installments": [],
  "created_at": "2026-06-04T10:00:00Z"
}
```

### Installment (ParcelaDespesa)

```json
{
  "id": 11,
  "installment_number": 2,
  "amount": "3000.00",
  "due_date": "2026-07-10",
  "is_paid": false,
  "paid_at": null,
  "status": "A_VENCER",
  "late_interest_cost": "0.00",
  "deferrals": []
}
```

## Enums aceitos

### frequency

- `ONE_TIME`
- `MONTHLY`
- `ANNUAL`

### category

- `ESTRUTURA`
- `PESSOAS`
- `IMPOSTOS`
- `OPERACIONAL`

### priority

- `LEGAL`
- `OPERACIONAL`
- `OPCIONAL`

## 1) Listar expenses

### Endpoint

```http
GET /api/expenses/
```

### Query params opcionais

- `year` (int)
- `month` (int)

### Comportamento

1. Sempre filtra por firm do usuario autenticado.
2. Sempre retorna apenas `is_active=true`.
3. Se `year` e `month` forem enviados juntos, retorna lista sem paginacao.
4. Sem `year/month`, usa fluxo padrao do ModelViewSet (pode vir paginado, conforme configuracao global).

### Exemplo

```http
GET /api/expenses/?year=2026&month=10
```

## 2) Criar expense

### Endpoint

```http
POST /api/expenses/
```

### Payload exemplo (avulso)

```json
{
  "title": "Internet",
  "description": "Plano escritorio",
  "amount": 299.90,
  "due_date": "2026-10-05",
  "frequency": "MONTHLY",
  "category": "OPERACIONAL",
  "priority": "OPERACIONAL",
  "is_paid": false,
  "is_active": true,
  "is_installment": false,
  "total_installments": 1,
  "interest_rate_month": 0
}
```

### Payload exemplo (parcelado)

```json
{
  "title": "Notebook Equipe",
  "description": "Compra parcelada",
  "amount": 6000.00,
  "due_date": "2026-10-10",
  "frequency": "ONE_TIME",
  "category": "ESTRUTURA",
  "priority": "OPERACIONAL",
  "is_paid": false,
  "is_active": true,
  "is_installment": true,
  "total_installments": 3,
  "interest_rate_month": 1.5
}
```

### Regras de criacao

1. `firm` e definido pelo backend via usuario autenticado.
2. Se `is_installment=true`, backend gera parcelas automaticamente.
3. Valor das parcelas e distribuido a partir de `amount` e `total_installments`.
4. Ajuste de centavos e aplicado na ultima parcela.
5. Datas de parcelas avancam mensalmente a partir de `due_date`.

## 3) Buscar expense por id

### Endpoint

```http
GET /api/expenses/{id}/
```

### Resposta

- Objeto completo de expense com `installments` embutido.

## 4) Atualizar expense

### Endpoint

```http
PATCH /api/expenses/{id}/
```

### Exemplo: marcar como pago

```json
{
  "is_paid": true
}
```

### Regra importante

- Ao marcar `is_paid=true`, backend define `paid_at` no header e em todas as parcelas.
- Ao voltar `is_paid=false`, backend limpa `paid_at` do header e das parcelas.

## 5) Remover expense

### Endpoint

```http
DELETE /api/expenses/{id}/
```

### Comportamento

- Remove o registro de expense.
- Parcelas relacionadas sao removidas por cascata.

## 6) Importacao em lote

### Endpoint

```http
POST /api/expenses/import/
```

### Payload

- Array de objetos de expense.

```json
[
  {
    "title": "Aluguel da Sala",
    "description": "Obs livre",
    "amount": 4800.00,
    "due_date": "2026-10-10",
    "frequency": "ONE_TIME",
    "category": "ESTRUTURA",
    "priority": "LEGAL",
    "is_active": true,
    "is_installment": false,
    "total_installments": 1,
    "installment_value": 4800.00,
    "interest_rate_month": 0
  }
]
```

### Regras de importacao implementadas

1. Payload deve ser array.
2. Limite maximo de 500 itens por request.
3. Processamento parcial: nunca aborta lote inteiro por erro em um item.
4. Retorno com dois arrays: `created` e `errors`.
5. `index` em `errors` usa base 0.
6. `is_active` e forcado para `true` no backend.
7. Se `category` vier `null`, backend normaliza para `OPERACIONAL`.
8. Se `installment_value` for enviado:
   - valida que `total_installments >= 1`
   - valida que `amount == installment_value * total_installments`
   - ajusta `is_installment=true` quando `total_installments >= 2`

### Resposta esperada

```json
{
  "created": [
    { "id": 1, "title": "Aluguel da Sala" }
  ],
  "errors": [
    { "index": 2, "detail": "Mensagem de erro para linha 2" }
  ]
}
```

## 7) Adiar parcela (deferral)

### Endpoint

```http
POST /api/expenses/defer-installment/{installment_id}/
```

### Payload exemplo

```json
{
  "new_date": "2026-11-15",
  "penalty_amount": 50.00
}
```

### Comportamento

1. Cria registro de adiamento (deferral) para a parcela.
2. Atualiza `due_date` da parcela para `new_date`.
3. Se `penalty_amount` for enviado, soma ao valor da parcela.
4. Retorna dados do deferral criado.

## 8) Resumo anual

### Endpoint

```http
GET /api/expenses/yearly-summary/
```

### Comportamento

1. Considera janela de aproximadamente 12 meses (de hoje para tras).
2. Agrupa por periodo `YYYY-MM`.
3. Retorna:
   - lista de expenses por mes
   - total por mes
   - bloco dashboard com entradas, a receber, saidas e saldo liquido
   - saldo total em conta

### Estrutura de resposta (resumo)

```json
{
  "summary": [
    {
      "period": "2026-10",
      "total_amount": 5099.9,
      "expenses": [],
      "dashboard": {
        "entradas_do_mes": 0,
        "a_receber": 0,
        "saidas_do_mes": 5099.9,
        "saldo_liquido": -5099.9
      }
    }
  ],
  "total_bank_balance": 12000.0
}
```

## Erros comuns e tratamento sugerido

1. `400 Payload deve ser um array de objetos.`
2. `400 Maximo de 500 registros por importacao.`
3. `400 O usuario nao possui nenhuma empresa vinculada...`
4. `400 amount deve ser igual a installment_value * total_installments.`
5. `400 year/month invalidos na listagem filtrada.`

No frontend, trate cada erro de import por item usando `errors[index]`.

## Checklist rapido para frontend

1. Sempre enviar token JWT.
2. Para import, enviar array e tratar `created` + `errors`.
3. Em parcelamento, confira consistencia de `amount`, `total_installments` e `installment_value`.
4. Ao usar listagem por mes, envie `year` e `month` juntos.
5. Ao marcar pago/nao pago, esperar reflexo em todas as parcelas.
