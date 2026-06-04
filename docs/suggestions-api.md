# Guia de uso da API de Sugestoes

Este documento descreve como consumir os endpoints de sugestoes e feedbacks.

## 1. Autenticacao

```http
Authorization: Bearer <seu_token>
Content-Type: application/json
```

Base URL:

```text
/api/suggestions/
```

## 2. O que sao as sugestoes

O modulo de sugestoes permite que usuarios da plataforma enviem feedbacks, reportem bugs e solicitem novas funcionalidades diretamente pelo app. Cada sugestao e vinculada a firm do usuario.

## 3. Estrutura de dados

### Suggestion

```json
{
  "id": 1,
  "name": "Maria da Silva",
  "email": "maria@exemplo.com",
  "category": "NOVA_FUNC",
  "category_display": "Nova Funcionalidade",
  "subject": "Exportar relatorio em PDF",
  "message": "Seria muito util poder exportar o relatorio mensal em PDF para enviar aos socios.",
  "created_at": "2026-06-04T10:00:00Z"
}
```

### Categorias

| Valor | Descricao |
|-------|-----------|
| `MELHORIA` | Melhoria de Funcionalidade |
| `NOVA_FUNC` | Nova Funcionalidade |
| `BUG` | Relato de Bug |
| `OUTRO` | Outro |

## 4. Listar sugestoes

```http
GET /api/suggestions/
```

Retorna as sugestoes da firm do usuario autenticado, ordenadas da mais recente.

## 5. Enviar sugestao

```http
POST /api/suggestions/
```

```json
{
  "name": "Joao Souza",
  "email": "joao@exemplo.com",
  "category": "BUG",
  "subject": "Erro ao salvar despesa parcelada",
  "message": "Quando tento salvar uma despesa com 12 parcelas, aparece erro 500."
}
```

Resposta `201`:

```json
{
  "id": 5,
  "name": "Joao Souza",
  "email": "joao@exemplo.com",
  "category": "BUG",
  "category_display": "Relato de Bug",
  "subject": "Erro ao salvar despesa parcelada",
  "message": "Quando tento salvar uma despesa com 12 parcelas, aparece erro 500.",
  "created_at": "2026-06-04T14:30:00Z"
}
```

A sugestao e automaticamente vinculada a firm do usuario autenticado.

## 6. Buscar sugestao por ID

```http
GET /api/suggestions/{id}/
```

## 7. Atualizar sugestao

```http
PATCH /api/suggestions/{id}/
```

## 8. Remover sugestao

```http
DELETE /api/suggestions/{id}/
```

## 9. Checklist rapido para o frontend

1. Sempre enviar token no header.
2. `name` e `email` no body sao do remetente — podem ser preenchidos automaticamente com os dados do perfil logado.
3. `category_display` retorna o label legivel em portugues — use para exibir na UI.
4. Sugestoes sao isoladas por firm — um usuario nao ve sugestoes de outros escritorios.
