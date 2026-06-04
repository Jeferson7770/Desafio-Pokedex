# Guia de uso da API de Honorarios

Este documento descreve como o frontend deve consumir os endpoints de Honorarios.

## 1. Autenticacao

Todos os endpoints exigem token JWT no header:

```http
Authorization: Bearer <seu_token>
Content-Type: application/json
```

Base URL:

```text
/api/honorarios/
```

## 2. Regras importantes antes de integrar

1. Multi-tenant por firm: o backend sempre usa a firm do usuario autenticado.
2. Filtro de data (`year` e/ou `month`) e opcional na listagem. Filtra por `due_date` das parcelas.
3. Para honorarios parcelados:
   - as parcelas sao geradas automaticamente no `POST`;
   - altere status do header para sincronizar todas as parcelas;
   - use o endpoint de installment para marcar parcelas individualmente.
4. Alterar `amount`, `date` ou `total_installments` recria todas as parcelas.
5. O campo `installment_value` e calculado automaticamente (amount / total_installments) e nao e enviado no POST.
6. Juros por atraso (`late_interest_cost`) e calculado dinamicamente por parcela — nao e armazenado no banco.

## 3. Estrutura de dados

### Honorario

```json
{
  "id": 1,
  "title": "Contrato Trabalhista - Cliente X",
  "amount": "9000.00",
  "date": "2026-06-01",
  "status": "PENDENTE",
  "notes": "",
  "is_installment": true,
  "total_installments": 3,
  "installment_value": 3000.0,
  "interest_rate_month": "2.00",
  "created_at": "2026-06-04T10:00:00Z",
  "installments": [
    {
      "id": 101,
      "installment_number": 1,
      "amount": "3000.00",
      "due_date": "2026-06-01",
      "status": "PENDENTE",
      "late_interest_cost": "0.00",
      "paid_at": null
    }
  ]
}
```

### Valores de status

| Campo | Opcoes |
|-------|--------|
| `status` (header) | `PENDENTE`, `RECEBIDO` |
| `status` (parcela) | `PENDENTE`, `RECEBIDO` |

## 4. Listar honorarios (GET)

```http
GET /api/honorarios/
GET /api/honorarios/?year=2026&month=6
GET /api/honorarios/?year=2026
```

Filtro e opcional. Quando informado, filtra pelos honorarios que possuem pelo menos uma parcela com `due_date` no periodo.

Resposta `200`:

```json
[
  { ...honorario... }
]
```

## 5. Criar honorario (POST)

### 5.1 Honorario sem parcelamento

```http
POST /api/honorarios/
```

```json
{
  "title": "Consulta juridica",
  "amount": "1500.00",
  "date": "2026-06-10",
  "status": "PENDENTE",
  "notes": "",
  "is_installment": false,
  "total_installments": 1,
  "interest_rate_month": "0.00"
}
```

Backend gera 1 parcela com `amount = 1500.00`, `due_date = 2026-06-10`.

### 5.2 Honorario parcelado

```json
{
  "title": "Contrato trabalhista",
  "amount": "9000.00",
  "date": "2026-06-01",
  "status": "PENDENTE",
  "notes": "",
  "is_installment": true,
  "total_installments": 3,
  "interest_rate_month": "2.00"
}
```

Backend distribui o valor total em 3 parcelas mensais. O valor de cada parcela e calculado via `amount / total_installments`, com o centavo residual indo para a ultima parcela.

Resposta `201`:

```json
{
  "id": 1,
  "installments": [
    { "installment_number": 1, "amount": "3000.00", "due_date": "2026-06-01", "status": "PENDENTE" },
    { "installment_number": 2, "amount": "3000.00", "due_date": "2026-07-01", "status": "PENDENTE" },
    { "installment_number": 3, "amount": "3000.00", "due_date": "2026-08-01", "status": "PENDENTE" }
  ]
}
```

## 6. Atualizar honorario (PATCH)

```http
PATCH /api/honorarios/{id}/
```

### 6.1 Alterar campos simples

```json
{
  "title": "Novo titulo",
  "notes": "Observacao atualizada"
}
```

### 6.2 Alterar status (sincroniza todas as parcelas)

```json
{
  "status": "RECEBIDO"
}
```

Todas as `ParcelaHonorario` associadas serao atualizadas para `RECEBIDO`.

### 6.3 Alterar valor ou estrutura (recria parcelas)

```json
{
  "amount": "12000.00",
  "total_installments": 4
}
```

Todas as parcelas existentes serao deletadas e recriadas com a nova estrutura.

## 7. Atualizar parcela individual (PATCH)

```http
PATCH /api/honorarios/{id}/installments/{installment_id}/
```

### 7.1 Marcar como recebida

```json
{
  "status": "RECEBIDO",
  "paid_at": "2026-06-04T14:00:00Z"
}
```

### 7.2 Reverter para pendente

```json
{
  "status": "PENDENTE",
  "paid_at": null
}
```

O backend nao recalcula o status do header automaticamente neste endpoint — apenas a parcela e atualizada.

## 8. Remover honorario (DELETE)

```http
DELETE /api/honorarios/{id}/
```

Remove o honorario e todas as parcelas em cascata. Retorna `204 No Content`.

## 9. Importacao em lote (POST)

```http
POST /api/honorarios/import/
```

Body: array de objetos com a mesma estrutura do POST individual.

```json
[
  {
    "title": "Honorario A",
    "amount": "2000.00",
    "date": "2026-06-01",
    "status": "PENDENTE",
    "is_installment": false,
    "total_installments": 1,
    "interest_rate_month": "0.00"
  }
]
```

Resposta:

```json
{
  "created": [ { ...honorario... } ],
  "errors": [
    { "index": 1, "detail": "campo: mensagem de erro" }
  ]
}
```

Regras:
1. Maximo de 500 itens por requisicao.
2. Nunca aborta o lote inteiro por 1 item invalido.
3. Retorna os dois arrays sempre, mesmo que um deles esteja vazio.

## 10. Checklist rapido para o frontend

1. Sempre enviar token no header.
2. Nao enviar `installment_value` no POST — o campo e somente leitura.
3. Para marcar 1 parcela individualmente, usar o endpoint de installment.
4. Para marcar todas de uma vez, alterar `status` no header via PATCH.
5. Alterar `amount`, `date` ou `total_installments` recria todas as parcelas.
6. Tratar erros de validacao (400) por campo/mensagem.
