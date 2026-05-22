# fincecore

🎯 **Backend da Fince** — API Django REST para gestão financeira de escritórios de advocacia.

Este repositório contém o servidor do Fince, responsável por:
- autenticação JWT;
- multi-firma e gestão de membros de escritório;
- controle de despesas, casos jurídicos, honorários e sugestões;
- projeção de cashflow;
- documentação OpenAPI com Swagger e Redoc.

---

## 💻 Tecnologias

- Python 3.12+
- Django 6.x
- Django REST Framework
- djangorestframework-simplejwt
- drf-spectacular
- python-decouple
- dj-database-url
- django-ratelimit
- psycopg / sqlite fallback

---

## 🚀 Como rodar localmente

### Pré-requisitos

- Python 3.12+
- Poetry instalado ou `pipx install poetry`
- Docker (opcional)

### Passo a passo

```bash
cd fincecore
poetry install
```

Crie um `.env` com pelo menos:

```env
SECRET_KEY="sua-chave-secreta"
DEBUG=True
DATABASE_URL="sqlite:///db.sqlite3"
```

Em seguida:

```bash
poetry run python manage.py migrate
poetry run python manage.py runserver 0.0.0.0:8000
```

A API ficará disponível em `http://localhost:8000`.

### Docker

```bash
docker build -t fincecore .
docker run -e SECRET_KEY="sua-chave-secreta" -p 8000:8000 fincecore
```

---

## 🧩 Arquitetura do backend

O backend é organizado em apps Django com responsabilidade bem definida:

- `src.users` — autenticação, registro, perfil de advogado, reset de senha
- `src.firms` — estrutura de escritórios e membros
- `src.expenses` — despesas, prioridades e adiamentos
- `src.cashflow` — projeções e resumo financeiro
- `src.cases` — casos jurídicos e cronograma de pagamentos
- `src.suggestions` — sugestões de melhoria e bugs
- `src.honorarios` — honorários financeiros do escritório
- `src.integrations` — espaço para integrações externas
- `src.transactions` — espaço para transações financeiras

O `core/settings.py` define:
- `AUTH_USER_MODEL = "users.User"`
- `SIMPLE_JWT` para tokens JWT
- `drf_spectacular` como gerador de schema
- fallback para SQLite via `DATABASE_URL`

---

## 🔐 Autenticação e dados de usuário

O projeto usa um modelo de usuário customizado:
- email único como login
- `username` removido
- senha com validação forte (8-16 chars, maiúscula, minúscula, número e caractere especial)

O fluxo de registro normaliza email e CPF antes de salvar e cria automaticamente o perfil de advogado.

### Observações importantes

- A rota de perfil do advogado está exposta como `/api/auth/laywer-profile/`.
- O `LogoutView` existe em `src/users/views/logout.py`, mas não está registrado em `src/users/urls.py`.

---

## 🌐 Endpoints principais

### Autenticação e usuário

- `POST /api/auth/register/` — criar conta + perfil de advogado
- `POST /api/auth/login/` — autenticar e receber tokens JWT
- `GET /api/auth/laywer-profile/` — ler o perfil do advogado autenticado
- `POST /api/auth/password-reset/` — solicitar reset de senha
- `POST /api/auth/password-reset-confirm/` — confirmar novo password

### Escritórios e membros

Base: `POST /api/firms/`, `GET /api/firms/`

- `GET /api/firms/` — lista escritórios do usuário
- `POST /api/firms/` — cria um escritório e adiciona o usuário como OWNER
- `GET /api/firms/{id}/` — detahes do escritório
- `PUT/PATCH /api/firms/{id}/` — atualizar escritório
- `DELETE /api/firms/{id}/` — remover escritório
- `GET /api/firms/{id}/members/` — listar membros do escritório
- `POST /api/firms/{id}/add_member/` — adicionar membro por email/role

### Despesas

Base: `POST /api/expenses/`, `GET /api/expenses/`

- CRUD padrão de despesas
- `POST /api/expenses/{id}/defer/` — adiar um vencimento e salvar histórico

### Cashflow

Base: `GET /api/cashflow/`

- `GET /api/cashflow/projection/?days=N` — projeção diária de receita x despesa
- `GET /api/cashflow/summary/` — resumo total de receitas, despesas e resultado líquido

### Casos jurídicos

Base: `POST /api/cases/`, `GET /api/cases/`

- `POST /api/cases/` — cria caso e agendas de pagamento
- `GET /api/cases/` — lista casos do escritório
- `GET /api/cases/{id}/` — detalhes do caso

### Sugestões

Base: `POST /api/suggestions/`, `GET /api/suggestions/`

- `POST /api/suggestions/` — enviar sugestão ou relato de bug
- `GET /api/suggestions/` — listar sugestões do escritório

### Honorários

Base: `POST /api/honorarios/`, `GET /api/honorarios/`

- `GET /api/honorarios/?year=YYYY&month=MM` — filtra honorários por ano/mês
- `POST /api/honorarios/` — cadastrar honorário

### Docs e schema

- `GET /api/schema/` — OpenAPI schema JSON
- `GET /api/docs/` — Swagger UI interativo
- `GET /api/redoc/` — documentação Redoc

---

## 🧠 Fluxos de dados importantes

### Multi-tenancy por escritório

Quase todos os viewsets amarram o usuário à firma via `request.user.firm_memberships.first().firm` ou `firm__members__user=request.user`. Isso mantém os dados isolados por escritório.

### `FirmCreateSerializer`

Ao criar um escritório, o backend também cria um `FirmMember` com papel `OWNER` automaticamente.

### `ExpenseViewSet`

- Cria despesas vinculadas à firma do usuário
- Marca `paid_at` automaticamente quando a despesa é atualizada para `is_paid=true`
- `defer` cria registro de adiamento e atualiza o `due_date`

### `CashflowService`

Gera projeções usando:
- despesas ativas com vencimento futuro
- agendas de pagamento de casos não pagos

### `CaseSerializer`

Permite payloads com `schedules` para criar vários cronogramas de pagamento de um caso em mesmo request.

---

## 🔧 Dicas para desenvolvedores

- Use `Authorization: Bearer <token>` em todas as chamadas autenticadas.
- Os campos de CPF e email são normalizados.
- `LawyerProfile` usa dados do escritório e é o núcleo do onboarding do usuário.
- Se quiser propor melhorias, o backend já possui rotas de API e OpenAPI prontas.

### Boilerplate útil

Exemplo de registro:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@fince.local",
    "password": "Senha@2026",
    "full_name": "Dev Fince",
    "cpf": "111.222.333-44",
    "oab_number": "12345",
    "oab_state": "SP"
  }'
```

Login:

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@fince.local",
    "password": "Senha@2026"
  }'
```

---

## 🧪 Testes

O backend ainda está no estágio inicial em relação a testes. Existem arquivos de teste vazios em `src/integrations/tests.py` e `src/transactions/tests.py`.

Se você for contribuir, uma ótima área de melhoria é adicionar cobertura de testes para:
- autenticação e registro
- multi-tenancy de escritórios
- criação/adiamento de despesas
- projeções de cashflow

---

## 🤝 Como contribuir

1. Fork este repositório.
2. Crie uma branch com prefixo `feature/`, `fix/` ou `chore/`.
3. Faça commits pequenos e claros.
4. Abra PR para `main` com descrição e contexto.
5. Se possível, adicione testes e documente novas rotas.

### Bons pontos para contributedores

- Corrigir o typo `laywer-profile` para `lawyer-profile` com cuidado
- Registrar `LogoutView` em `src/users/urls.py`
- Adicionar testes unitários e de integração
- Melhorar o fluxo de reset de senha para ambiente de produção
- Adicionar suporte real para `integrations` e `transactions`

---

## 📌 Observações finais

- O backend funciona bem como API REST autônoma para o frontend React.
- A documentação já está habilitada via Swagger e Redoc.
- A política de dados e a separação por firma são pontos fortes para quem está contribuindo.

Boa codificação! 🚀
