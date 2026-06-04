# Guia de uso da API de Usuarios

Este documento descreve como consumir os endpoints de autenticacao, perfil de advogado, assinatura e notificacoes.

## 1. Base URLs

```text
/api/users/register/
/api/users/login/
/api/users/logout/
/api/users/laywer-profile/
/api/users/billing/subscription/
/api/users/notifications/settings/
```

---

## 2. Registro

```http
POST /api/users/register/
```

Nao requer autenticacao.

```json
{
  "email": "advogado@exemplo.com",
  "password": "Senha@Forte123",
  "full_name": "Maria da Silva",
  "cpf": "123.456.789-09",
  "oab_number": "123456",
  "oab_state": "SP"
}
```

Validacoes:
- `email`: formato valido, sem duplicata no sistema.
- `password`: deve atender requisitos de forca (validado pelo backend).
- `cpf`: formato valido, sem duplicata no sistema.

Resposta `201`:

```json
{
  "email": "advogado@exemplo.com",
  "full_name": "Maria da Silva"
}
```

O backend cria o `User` e o `LawyerProfile` em transacao atomica.

---

## 3. Login

```http
POST /api/users/login/
```

Nao requer autenticacao.

```json
{
  "email": "advogado@exemplo.com",
  "password": "Senha@Forte123"
}
```

Resposta `200`:

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Use o `access` token no header `Authorization: Bearer <token>` para todas as requisicoes autenticadas.

---

## 4. Logout

```http
POST /api/users/logout/
```

Requer autenticacao. Invalida o token de refresh.

---

## 5. Perfil do advogado

### 5.1 Buscar perfil

```http
GET /api/users/laywer-profile/
```

Retorna o perfil completo incluindo dados pessoais, OAB, configuracoes de escritorio, assinatura e dispositivos.

Resposta `200`:

```json
{
  "email": "advogado@exemplo.com",
  "full_name": "Maria da Silva",
  "phone": "11999999999",
  "oab_number": "123456",
  "oab_state": "SP",
  "cpf": "123.456.789-09",
  "birth_date": "1990-05-15",
  "years_of_experience": 7,
  "tax_regime": "SIMPLES",
  "cep": "01310-100",
  "street": "Av. Paulista",
  "number": "1000",
  "complement": "Sala 501",
  "neighborhood": "Bela Vista",
  "city": "Sao Paulo",
  "state": "SP",
  "office_type": "PHYSICAL",
  "practice_areas": ["Trabalhista", "Previdenciario"],
  "has_employees": true,
  "average_monthly_income": "12000.00",
  "average_monthly_expense": "4500.00",
  "income_variability": "MEDIUM",
  "has_bank_connected": true,
  "goal_type": "STABILITY",
  "financial_goal": "8000.00",
  "onboarding_completed": true,
  "is_active": true,
  "devices": [ ... ],
  "billing": { ... },
  "notifications": { ... },
  "office_profile": {
    "office_name": "Silva & Associados",
    "cnpj_or_cpf": "123.456.789-09",
    "contact_email": "advogado@exemplo.com",
    "tax_regime_display": "Simples Nacional",
    "tax_regime": "SIMPLES"
  },
  "created_at": "2026-01-10T10:00:00Z"
}
```

### 5.2 Criar perfil

```http
POST /api/users/laywer-profile/
```

Usado no onboarding, apos o registro. Nao e possivel criar um segundo perfil para o mesmo usuario.

### 5.3 Atualizar perfil

```http
PATCH /api/users/laywer-profile/
PUT /api/users/laywer-profile/
```

Envie apenas os campos que deseja alterar no PATCH.

### 5.4 Alterar senha

```http
POST /api/users/laywer-profile/change-password/
```

```json
{
  "current_password": "SenhaAtual123",
  "new_password": "NovaSenha@456"
}
```

Comportamento:
1. Valida a senha atual.
2. Atualiza a senha.
3. Invalida todos os tokens de refresh ativos (desconecta todos os dispositivos).
4. Retorna novo par de tokens `access` + `refresh`.

### 5.5 Desconectar dispositivo

```http
POST /api/users/laywer-profile/disconnect-device/{device_pk}/
```

### 5.6 Desconectar todos os dispositivos

```http
POST /api/users/laywer-profile/disconnect-all-devices/
```

### 5.7 Deletar conta

```http
POST /api/users/laywer-profile/delete-account/
```

Remove o usuario e todos os dados associados. Acao irreversivel.

---

## 6. Regimes tributarios

| Valor | Descricao |
|-------|-----------|
| `SIMPLES` | Simples Nacional |
| `LUCRO_PRESUMIDO` | Lucro Presumido |
| `LUCRO_REAL` | Lucro Real |
| `AUTONOMO_PF` | Autonomo (Pessoa Fisica) |

## 7. Variaveis de perfil

### Variabilidade de renda (`income_variability`)

| Valor | Descricao |
|-------|-----------|
| `LOW` | Baixa - Previsivel |
| `MEDIUM` | Media - Alguma variacao |
| `HIGH` | Alta - Muito variavel |

### Objetivo financeiro (`goal_type`)

| Valor | Descricao |
|-------|-----------|
| `SURVIVAL` | Sobrevivencia - Quitar dividas e manter o escritorio |
| `STABILITY` | Estabilidade - Construir pratica financeira solida |
| `GROWTH` | Crescimento - Escalar o escritorio |

---

## 8. Assinatura (Billing)

### 8.1 Buscar assinatura atual

```http
GET /api/users/billing/subscription/
```

Resposta:

```json
{
  "id": 1,
  "status": "ACTIVE",
  "cancel_at_period_end": false,
  "next_renewal": "04/07/2026",
  "is_premium_active": true,
  "plan_details": {
    "id": 1,
    "name": "Pro Mensal",
    "price": "99.90",
    "interval": "MONTHLY"
  },
  "gateway_customer_id": "cus_abc123"
}
```

Status possiveis: `ACTIVE`, `CANCELED`, `PAST_DUE`, `TRIALING`.

`is_premium_active` e `true` se `ACTIVE` ou `TRIALING`, ou se `CANCELED` mas ainda dentro do periodo pago.

### 8.2 Solicitar upgrade

```http
POST /api/users/billing/subscription/upgrade/
```

```json
{
  "plan_id": 2
}
```

Retorna `501` — integracao com gateway pendente.

### 8.3 Solicitar cancelamento

```http
POST /api/users/billing/subscription/cancel/
```

Retorna `501` — integracao com gateway pendente.

---

## 9. Configuracoes de notificacao

### 9.1 Buscar configuracoes

```http
GET /api/users/notifications/settings/
```

Resposta:

```json
{
  "id": 1,
  "enable_due_alerts": true,
  "days_advance_taxes": 5,
  "days_advance_rent": 3,
  "days_advance_others": 1,
  "enable_approval_requests": true,
  "enable_weekly_summary": true
}
```

### 9.2 Atualizar configuracoes

```http
PATCH /api/users/notifications/settings/
```

```json
{
  "enable_weekly_summary": false,
  "days_advance_taxes": 7
}
```

---

## 10. Checklist rapido para o frontend

1. Fluxo inicial: `POST /register/` → `POST /login/` → salvar tokens → `POST /laywer-profile/` (onboarding).
2. Renovar `access` token com o `refresh` via endpoint padrao do SimpleJWT (`/api/token/refresh/`).
3. Apos alterar senha, os tokens antigos sao invalidos — atualizar os tokens em storage.
4. `has_bank_connected` no perfil indica se a firm ja tem Open Finance conectado.
5. `onboarding_completed` controla se o onboarding foi finalizado.
6. Billing endpoints de upgrade/cancel retornam 501 por enquanto.
