# Recuperação de Senha — Spec de Implementação

Fluxo completo de recuperação de senha via email com código de 6 dígitos. O usuário não precisa clicar em link — digita o código diretamente no app.

---

## 1. Fluxo do Usuário

```
[Tela de login]
      │
      ▼
"Esqueci minha senha"
      │
      ▼
[1] Informa o email
      │
      ▼  POST /api/auth/password/forgot/
      │
      ▼
Recebe email com código de 6 dígitos (expira em 15 min)
      │
      ▼
[2] Digita o código no app
      │
      ▼  POST /api/auth/password/verify-code/
      │
      ▼
Recebe reset_token temporário
      │
      ▼
[3] Define nova senha
      │
      ▼  POST /api/auth/password/reset/
      │
      ▼
Senha atualizada → redirecionado para login
```

---

## 2. Modelo de Dados

### `PasswordResetCode`

Novo model em `src/users/models/password_reset.py`:

```python
import uuid
from django.db import models
from django.utils import timezone
from .user import User

EXPIRY_MINUTES = 15
MAX_ATTEMPTS = 5


class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_codes")
    code_hash = models.CharField(max_length=64)           # HMAC-SHA256 do código
    reset_token = models.UUIDField(null=True, blank=True) # preenchido após verificação bem-sucedida
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired() and self.attempts < MAX_ATTEMPTS
```

**Por que HMAC no código?**
O código de 6 dígitos é guardado como `HMAC-SHA256(code, SECRET_KEY)` — se o banco vazar, ninguém consegue os códigos ativos.

**Por que `reset_token` separado?**
Após verificar o código, o frontend precisa de um token para a etapa 3. Um UUID garante que o código de 6 dígitos não fica circulando além do necessário.

---

## 3. Endpoints

### 3.1 `POST /api/auth/password/forgot/`

Solicita o envio do código de recuperação.

**Permissão:** AllowAny  
**Rate limit:** 3 requisições por IP/minuto + 3 por email/hora

**Request:**
```json
{ "email": "advogado@escritorio.com.br" }
```

**Lógica interna:**
1. Busca `User` pelo email.
2. Se não encontrar → retorna `200` com resposta genérica (não revela se email existe).
3. Se usuário tem senha inutilizável (cadastro via Google) → retorna `200` com instrução específica.
4. Invalida códigos anteriores não usados do mesmo usuário (marca como `is_used=True`).
5. Gera código numérico aleatório de 6 dígitos (`secrets.randbelow`).
6. Salva `PasswordResetCode` com `code_hash = HMAC(code)` e `expires_at = now + 15min`.
7. Dispara `EmailService().enviar_codigo_reset(email, nome, code)` em background thread.
8. Rastreia `senha_reset_solicitado` no PostHog.

**Response `200` (todos os casos — nunca revela se email existe):**
```json
{
  "detail": "Se este email estiver cadastrado, você receberá um código em instantes."
}
```

**Caso especial — usuário do Google (response `200`):**
```json
{
  "detail": "Esta conta foi criada com Google. Acesse usando o botão 'Entrar com Google'.",
  "method": "google"
}
```

---

### 3.2 `POST /api/auth/password/verify-code/`

Valida o código de 6 dígitos e retorna um token para a etapa de redefinição.

**Permissão:** AllowAny  
**Rate limit:** 10 requisições por IP/minuto (a proteção principal é `MAX_ATTEMPTS` no DB)

**Request:**
```json
{
  "email": "advogado@escritorio.com.br",
  "code": "482917"
}
```

**Lógica interna:**
1. Busca o `PasswordResetCode` mais recente para o email que seja válido (`is_used=False`, não expirado, `attempts < MAX_ATTEMPTS`).
2. Se não encontrar registro → `400`.
3. Verifica `HMAC(code_informado) == code_hash`.
4. Se inválido: incrementa `attempts`, salva. Se `attempts >= MAX_ATTEMPTS`, retorna erro de bloqueio.
5. Se válido: gera `reset_token = uuid4()`, salva no registro com `is_verified=True`.
6. Rastreia `senha_codigo_verificado` no PostHog.
7. Retorna o `reset_token`.

**Response `200`:**
```json
{
  "reset_token": "a3f8c2d1-7b4e-4f9a-8c1d-2e3f4a5b6c7d"
}
```

**Errors:**
```json
// código inválido (ainda tem tentativas)
{ "detail": "Código incorreto. Você tem X tentativa(s) restante(s)." }

// código expirado
{ "detail": "Este código expirou. Solicite um novo." }

// bloqueado por excesso de tentativas
{ "detail": "Muitas tentativas incorretas. Solicite um novo código." }

// nenhum código ativo encontrado
{ "detail": "Nenhum código ativo encontrado para este email." }
```

---

### 3.3 `POST /api/auth/password/reset/`

Redefine a senha usando o `reset_token` obtido na etapa anterior.

**Permissão:** AllowAny  
**Rate limit:** 5 requisições por IP/minuto

**Request:**
```json
{
  "reset_token": "a3f8c2d1-7b4e-4f9a-8c1d-2e3f4a5b6c7d",
  "new_password": "MinhaNovaS3nh@"
}
```

**Lógica interna:**
1. Busca `PasswordResetCode` por `reset_token` que seja `is_verified=True`, `is_used=False` e não expirado.
2. Se não encontrar → `400`.
3. Valida `new_password` com `validate_password_strength()` (regras já existentes: 8–16 chars, maiúscula, minúscula, número, especial).
4. Chama `user.set_password(new_password)` e `user.save()`.
5. Marca o código como `is_used=True`.
6. Invalida todos os refresh tokens ativos do usuário (limpa sessões abertas) — via `OutstandingToken`.
7. Rastreia `senha_redefinida` no PostHog.
8. Retorna `200`.

**Response `200`:**
```json
{
  "detail": "Senha atualizada com sucesso. Faça login com sua nova senha."
}
```

**Errors:**
```json
// token inválido, expirado ou já usado
{ "detail": "Link de redefinição inválido ou expirado. Solicite um novo código." }

// senha fraca
{ "new_password": ["A senha deve ter entre 8 e 16 caracteres"] }
```

---

## 4. Arquivos a Criar / Modificar

```
src/users/
├── models/
│   └── password_reset.py          ← novo: PasswordResetCode
├── views/
│   └── password_reset.py          ← novo: 3 views
├── services/
│   └── email_service.py           ← adicionar: enviar_codigo_reset()
└── urls.py                        ← adicionar: 3 rotas
```

### Rotas a adicionar em `src/users/urls.py`:

```python
from .views.password_reset import ForgotPasswordView, VerifyCodeView, ResetPasswordView

path('password/forgot/', ForgotPasswordView.as_view()),
path('password/verify-code/', VerifyCodeView.as_view()),
path('password/reset/', ResetPasswordView.as_view()),
```

---

## 5. Email — Código de Recuperação

Enviado via `EmailService.enviar_codigo_reset(user_email, user_name, code)`.

### Design

Segue as cores da marca (mesmo padrão do email de boas-vindas):

```
┌─────────────────────────────────────────┐
│  [header dark #0D1117]                  │
│       Fince.  ←  logo verde             │
│   Recuperação de senha 🔐               │
│   "Oi, {nome}! Recebemos seu pedido"   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Seu código de verificação:             │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  │      4  8  2  9  1  7             │  │
│  │  (fundo dark, dígitos verde lima) │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ⏱ Este código expira em 15 minutos.   │
│                                         │
│  Se você não solicitou esta            │
│  recuperação, ignore este email.        │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  © 2026 Fince · suafince.com.br        │
└─────────────────────────────────────────┘
```

**Destaque visual do código:**
- Fundo: `#0D1117` (dark)
- Dígitos: `#B2E62A` (verde lima), fonte monospace, tamanho 40px, espaçados
- Border-radius 14px
- Cada dígito separado visualmente para fácil leitura no celular

---

## 6. Segurança

| Proteção | Mecanismo |
|---|---|
| Não revelar se email existe | Response 200 genérico no `/forgot/` |
| Código de força bruta | `MAX_ATTEMPTS = 5` — bloqueia o código após 5 erros |
| Código expirável | `expires_at = now + 15 min` — nunca reutilizável depois |
| Código hasheado | `HMAC-SHA256(code, SECRET_KEY)` no banco |
| Token de uso único | `is_used=True` imediatamente após `/reset/` |
| Rate limit por IP | `django-ratelimit` nas 3 rotas |
| Invalidar sessões | `OutstandingToken.objects.filter(user=user).delete()` no `/reset/` |
| Google OAuth | Detecta `has_usable_password()` e responde adequadamente |
| Códigos paralelos | `/forgot/` invalida códigos anteriores antes de criar novo |

---

## 7. PostHog — Eventos Rastreados

| Evento | Quando | Propriedades |
|---|---|---|
| `senha_reset_solicitado` | Email enviado com sucesso | `user_id`, `metodo: "email"` |
| `senha_reset_google_bloqueado` | Usuário Google tenta reset | `user_email` |
| `senha_codigo_verificado` | Código correto | `user_id` |
| `senha_codigo_falha` | Código errado | `user_id`, `tentativas_restantes` |
| `senha_codigo_bloqueado` | MAX_ATTEMPTS atingido | `user_id` |
| `senha_redefinida` | Senha alterada com sucesso | `user_id` |

---

## 8. Migration

Após criar o model, rodar:

```bash
python manage.py makemigrations users --name add_password_reset_code
python manage.py migrate

# Railway:
railway run python manage.py migrate
```

---

## 9. Checklist de Implementação

- [ ] Criar `src/users/models/password_reset.py` com `PasswordResetCode`
- [ ] Registrar o model no `src/users/models/__init__.py`
- [ ] Criar migration e aplicar local + Railway
- [ ] Criar `src/users/views/password_reset.py` com `ForgotPasswordView`, `VerifyCodeView`, `ResetPasswordView`
- [ ] Adicionar método `enviar_codigo_reset()` em `email_service.py` com template HTML do código
- [ ] Registrar as 3 rotas em `src/users/urls.py`
- [ ] Testar fluxo completo: solicitar → receber email → verificar → redefinir → logar com nova senha
- [ ] Testar caso Google OAuth (deve retornar mensagem específica)
- [ ] Testar expiração (testar com código de 15 min expirado)
- [ ] Testar bloqueio por MAX_ATTEMPTS (5 tentativas erradas)
- [ ] Verificar que sessões antigas são invalidadas após reset
- [ ] Deploy no Railway
