# Guia de uso da API de Dinheiro (Contas, Transacoes e Dashboard)

Este documento descreve como consumir os endpoints do modulo financeiro: contas bancarias, transacoes e dashboard de resumo.

## 1. Autenticacao

```http
Authorization: Bearer <seu_token>
Content-Type: application/json
```

Base URLs:

```text
/api/finance/accounts/
/api/finance/transactions/
/api/finance/dashboard-summary/
```

---

## 2. Contas bancarias (BankAccount)

### 2.1 Estrutura

```json
{
  "id": 1,
  "firm": 10,
  "name": "Itau Escritorio",
  "account_type": "CHECKING",
  "provider_name": "Itau",
  "external_account_id": "abc-123",
  "initial_balance": "0.00",
  "current_balance": "15420.50",
  "created_at": "2026-06-01T10:00:00Z"
}
```

Tipos de conta (`account_type`):

| Valor | Descricao |
|-------|-----------|
| `CHECKING` | Conta Corrente |
| `SAVINGS` | Poupanca |
| `INVESTMENT` | Investimentos |
| `CASH` | Dinheiro em Especie |

### 2.2 Listar contas

```http
GET /api/finance/accounts/
```

Retorna apenas as contas da firm do usuario autenticado.

### 2.3 Criar conta manual

```http
POST /api/finance/accounts/
```

```json
{
  "name": "Caixinha Escritorio",
  "account_type": "CASH",
  "initial_balance": "500.00"
}
```

`current_balance` e `firm` sao preenchidos automaticamente pelo backend.

### 2.4 Atualizar conta

```http
PATCH /api/finance/accounts/{id}/
```

`current_balance` nao pode ser alterado diretamente — e atualizado via transacoes.

### 2.5 Remover conta

```http
DELETE /api/finance/accounts/{id}/
```

---

## 3. Open Finance (Pluggy)

### 3.1 Gerar connect token

```http
POST /api/finance/accounts/pluggy/connect-token/
```

Retorna um token temporario para abrir o widget de conexao bancaria no frontend.

Resposta `200`:

```json
{
  "connect_token": "eyJhbGciOi..."
}
```

Use esse token no widget do Pluggy para o usuario conectar a conta bancaria.

### 3.2 Sincronizar contas

```http
POST /api/finance/accounts/pluggy/sincronizar/
```

```json
{
  "item_id": "pluggy-item-uuid"
}
```

Comportamento:
1. Aguarda o item do Pluggy finalizar atualizacao (timeout de 45s).
2. Sincroniza saldos de todas as contas do item em transacao atomica.
3. Dispara busca de transacoes do mes atual em segundo plano (nao bloqueia a resposta).

Resposta `200`:

```json
{
  "message": "Os dados das contas foram carregados. As transacoes estao sendo sincronizadas em segundo plano e apareceracao em breve.",
  "accounts": [ { ...conta... } ]
}
```

Resposta `202` (ainda processando):

```json
{
  "message": "A sincronizacao bancaria ainda esta em processamento. Tente novamente em alguns segundos.",
  "item_status": "UPDATING"
}
```

### 3.3 Atualizar saldos do dashboard

```http
POST /api/finance/accounts/pluggy/atualizar-dashboard/
```

Rota auxiliar. Retorna mensagem de confirmacao sem bloquear.

---

## 4. Transacoes (Transaction)

### 4.1 Estrutura

```json
{
  "id": 1,
  "account": 1,
  "account_name": "Itau Escritorio",
  "description": "Pagamento honorario cliente X",
  "amount": "3000.00",
  "transaction_type": "INFLOW",
  "date": "2026-06-04",
  "expense_installment": null,
  "fee_installment": 101,
  "external_transaction_id": null,
  "is_reconciled": false,
  "created_at": "2026-06-04T10:00:00Z"
}
```

Tipos de transacao:

| Valor | Descricao |
|-------|-----------|
| `INFLOW` | Receita (Entrada) |
| `OUTFLOW` | Despesa (Saida) |

### 4.2 Listar transacoes

```http
GET /api/finance/transactions/
```

### 4.3 Criar transacao manual

```http
POST /api/finance/transactions/
```

```json
{
  "account": 1,
  "description": "Reembolso taxa judicial",
  "amount": "350.00",
  "transaction_type": "INFLOW",
  "date": "2026-06-04"
}
```

Ao criar:
- `INFLOW` soma ao `current_balance` da conta.
- `OUTFLOW` subtrai do `current_balance` da conta.

Restricao: nao e possivel vincular `expense_installment` e `fee_installment` ao mesmo tempo.

### 4.4 Remover transacao

```http
DELETE /api/finance/transactions/{id}/
```

O `current_balance` da conta e revertido automaticamente.

### 4.5 Resumo de fluxo de caixa

```http
GET /api/finance/transactions/cash-flow-summary/
```

Resposta:

```json
{
  "total_inflows": 18000.0,
  "total_outflows": 5200.0,
  "net_cash_flow": 12800.0,
  "total_bank_balance": 22400.0,
  "received_fees_current_month": 9000.0,
  "total_financial_availability": 31400.0,
  "top_five_transactions_current_month": [ ... ]
}
```

---

## 5. Dashboard de resumo financeiro

```http
GET /api/finance/dashboard-summary/
GET /api/finance/dashboard-summary/?year=2026&month=6
```

Parametros opcionais: `year` e `month`. Se omitidos, usa o mes atual.

Resposta `200`:

```json
{
  "ano_referencia": 2026,
  "mes_referencia": 6,
  "entradas_do_mes": 9000.0,
  "a_receber": 6000.0,
  "saidas_do_mes": 3200.0,
  "saldo_liquido": 5800.0,
  "saldo_em_conta": 22400.0
}
```

### Origem de cada campo

| Campo | Origem |
|-------|--------|
| `entradas_do_mes` | Soma de `ParcelaHonorario` com `status=RECEBIDO` + `OutraEntradaInstallment` com `status=RECEBIDO`, filtrados por `due_date` no mes |
| `a_receber` | Soma de `ParcelaHonorario` com `status=PENDENTE` + `OutraEntradaInstallment` com `status=PENDENTE`, filtrados por `due_date` no mes |
| `saidas_do_mes` | Soma de `ParcelaDespesa` com `is_paid=False` e `expense.is_active=True`, filtradas por `due_date` no mes |
| `saldo_liquido` | `entradas_do_mes - saidas_do_mes` |
| `saldo_em_conta` | Soma de `current_balance` de todas as `BankAccount` da firm |

---

## 6. Checklist rapido para o frontend

1. Sempre enviar token no header.
2. Para Open Finance: gerar connect token → usuario conecta no widget → chamar `/pluggy/sincronizar/` com o `item_id`.
3. Transacoes importadas via Open Finance chegam com `is_reconciled: true` e `external_transaction_id` preenchido.
4. Criacao e remocao de transacoes manuais ajustam `current_balance` automaticamente.
5. Dashboard usa `year`+`month` opcionais — sem filtro retorna o mes atual.
6. `saldo_liquido` reflete apenas entradas recebidas menos saidas nao pagas no mes.
