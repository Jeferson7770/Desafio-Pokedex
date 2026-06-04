# Guia de uso da API de Firms (Escritorios)

Este documento descreve como consumir os endpoints de escritorios e membros.

## 1. Autenticacao

```http
Authorization: Bearer <seu_token>
Content-Type: application/json
```

Base URL:

```text
/api/firms/
```

## 2. Regras importantes

1. Um usuario pode pertencer a multiplas firms, mas o sistema usa sempre a primeira membership.
2. Ao criar uma firm, o usuario criador e automaticamente associado como `OWNER`.
3. Um usuario so ve firms das quais e membro.

## 3. Estrutura de dados

### Firm

```json
{
  "id": 10,
  "name": "Silva & Associados",
  "type": "OFFICE",
  "created_at": "2026-01-10T10:00:00Z"
}
```

Tipos de escritorio (`type`):

| Valor | Descricao |
|-------|-----------|
| `SOLO` | Individual |
| `OFFICE` | Escritorio Coletivo |

### FirmMember

```json
{
  "id": 5,
  "user": 2,
  "user_email": "joao@exemplo.com",
  "role": "LAWYER",
  "created_at": "2026-02-01T10:00:00Z"
}
```

Papeis de membro (`role`):

| Valor | Descricao |
|-------|-----------|
| `OWNER` | Dono |
| `LAWYER` | Advogado Associado |
| `STAFF` | Equipe de Apoio |

## 4. Listar escritorios

```http
GET /api/firms/
```

Retorna os escritorios nos quais o usuario autenticado e membro.

## 5. Criar escritorio

```http
POST /api/firms/
```

```json
{
  "name": "Souza Advogados",
  "type": "SOLO"
}
```

Resposta `201`:

```json
{
  "id": 11,
  "name": "Souza Advogados",
  "type": "SOLO",
  "created_at": "2026-06-04T10:00:00Z"
}
```

O usuario que criou e adicionado como `OWNER` automaticamente.

## 6. Buscar escritorio por ID

```http
GET /api/firms/{id}/
```

## 7. Atualizar escritorio

```http
PATCH /api/firms/{id}/
```

```json
{
  "name": "Novo Nome do Escritorio"
}
```

## 8. Remover escritorio

```http
DELETE /api/firms/{id}/
```

Remove o escritorio e todos os dados relacionados em cascata. Use com cuidado.

## 9. Listar membros

```http
GET /api/firms/{id}/members/
```

Retorna todos os membros do escritorio.

Resposta `200`:

```json
[
  {
    "id": 1,
    "user": 1,
    "user_email": "dono@exemplo.com",
    "role": "OWNER",
    "created_at": "2026-01-10T10:00:00Z"
  },
  {
    "id": 2,
    "user": 3,
    "user_email": "associado@exemplo.com",
    "role": "LAWYER",
    "created_at": "2026-03-01T10:00:00Z"
  }
]
```

## 10. Adicionar membro

```http
POST /api/firms/{id}/add_member/
```

```json
{
  "user": 5,
  "role": "STAFF"
}
```

Resposta `201` com o objeto do membro criado.

## 11. Checklist rapido para o frontend

1. Sempre enviar token no header.
2. Na criacao da firm, o usuario ja fica como `OWNER` automaticamente.
3. Para convidar novos membros, usar `POST /api/firms/{id}/add_member/` com o `user` ID e o `role`.
4. Tratar erros 400 por campo nas validacoes.
