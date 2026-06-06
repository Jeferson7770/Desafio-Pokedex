# Guia de uso da API de Relatorios Financeiros

Este documento descreve como consumir os endpoints de relatorios financeiros consolidados.

## 1. Autenticacao

```http
Authorization: Bearer <seu_token>
Content-Type: application/json
```

Base URL:

```text
/api/reports/
```

## 2. O que sao os relatorios

O modulo de relatorios armazena snapshots consolidados da saude financeira da firm por mes/ano. Diferente do dashboard (que calcula em tempo real), os relatorios trabalham com dados ja processados e categorizados pelo backend.

Caso nao exista um relatorio consolidado para o periodo solicitado, o backend retorna um objeto vazio (zerado) sem erro.

## 3. Estrutura de dados

### FinancialReportSummary

```json
{
  "id": 1,
  "firm": 10,
  "month": 6,
  "year": 2026,
  "total_revenue": "18000.00",
  "total_expense": "7200.00",
  "expenses_fixed": "3500.00",
  "expenses_variable": "1800.00",
  "expenses_eventual": "900.00",
  "expenses_payroll": "4200.00",
  "expenses_taxes": "1100.00",
  "expenses_structure": "2000.00",
  "expenses_late_interest": "150.00",
  "team_size": 3,
  "last_sync_at": "2026-06-04T10:00:00Z",
  "is_fully_categorized": true
}
```

Campos calculados (nao estao no JSON, mas estao no modelo):

| Campo | Formula |
|-------|---------|
| `net_result` | `total_revenue - total_expense` |
| `profit_margin` | `(net_result / total_revenue) * 100` |

## 4. Buscar relatorio do mes

```http
GET /api/reports/
GET /api/reports/?year=2026&month=6
```

Parametros opcionais: `year` e `month`. Se omitidos, usa o mes atual.

Comportamento:
- Se existir relatorio consolidado para o periodo: retorna o objeto com os dados reais.
- Se nao existir: retorna objeto zerado sem erro (`total_revenue: 0`, etc.).

Resposta `200`:

```json
{
  "id": 1,
  "firm": 10,
  "month": 6,
  "year": 2026,
  "total_revenue": "18000.00",
  "total_expense": "7200.00",
  ...
}
```

## 5. Consolidar relatorio (POST / upsert)

```http
POST /api/reports/
```

Comportamento de upsert: se ja existir relatorio para a firm/mes/ano, atualiza; caso contrario, cria.

```json
{
  "month": 6,
  "year": 2026,
  "total_revenue": "18000.00",
  "total_expense": "7200.00",
  "expenses_fixed": "3500.00",
  "expenses_variable": "1800.00",
  "expenses_eventual": "900.00",
  "expenses_payroll": "4200.00",
  "expenses_taxes": "1100.00",
  "expenses_structure": "2000.00",
  "expenses_late_interest": "150.00",
  "team_size": 3,
  "is_fully_categorized": true
}
```

Resposta:
- `201 Created` se o relatorio foi criado.
- `200 OK` se foi atualizado.

## 6. Categorias de despesa

| Campo | Descricao |
|-------|-----------|
| `expenses_fixed` | Despesas fixas recorrentes |
| `expenses_variable` | Despesas variaveis |
| `expenses_eventual` | Despesas eventuais/extraordinarias |
| `expenses_payroll` | Pessoas e folha de pagamento |
| `expenses_taxes` | Impostos e tributos |
| `expenses_structure` | Estrutura e custo do escritorio |
| `expenses_late_interest` | Juros acumulados por atraso |

## 7. Checklist rapido para o frontend

1. `GET /api/reports/?year=2026&month=6` para carregar o relatorio do mes.
2. Nao tratar resposta zerada como erro — e o comportamento esperado para meses sem dados.
3. `POST /api/reports/` para consolidar dados ao fechar o mes (upsert automatico).
4. `is_fully_categorized: true` indica que todas as despesas foram categorizadas e o relatorio e confiavel.
5. `last_sync_at` indica quando os dados foram sincronizados pela ultima vez.
