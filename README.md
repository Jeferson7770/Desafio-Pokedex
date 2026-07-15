<<<<<<< HEAD
# fincecore

Official Fince backend: a financial management platform for lawyers and law firms.

We are a private company operating this product in production. This repository is open source because we believe in public development with production-grade standards.

We want to attract developers who enjoy solving real B2B financial product problems. Consistent contributors get on our hiring radar.

## Our open source vision

Fince is a startup in growth mode. We chose open source to build long-term technology with:

- technical transparency to build trust in the product
- community collaboration to accelerate quality and innovation
- open standards to simplify integrations and audits
- an ecosystem around a common foundation

We do not open source for marketing. We do it because the product gets better when development is public, reviewable, and driven by real user and integration needs.

## AGPLv3 licensing

This project is licensed under the GNU Affero General Public License v3.0 (AGPLv3), with the "or later" option.

In practice, this means:

- you can use, study, modify, and redistribute this code
- if you distribute modified versions, you must keep the same license
- if you run a modified version as a network service, you must provide the corresponding source code to users of that service

Official license file: `LICENSE`.

If your company needs different distribution/compliance terms, talk to the Fince team before production usage.

## What this project solves

FinceCore centralizes the business engine for:

- financial organization for law offices
- expense, fees, and other income management
- cash-flow monitoring and business indicators
- multi-firm structure with member-level permissions
- integration with external financial and payment providers

## Core API capabilities

### Authentication and account

- JWT with email/password login
- legal profile onboarding
- device management and account security

Base: `/api/auth/`

### Firms and members

- firm creation
- member invitation/addition
- per-firm data isolation

Base: `/api/firms/`

### Operational finance

- bank accounts and transactions
- consolidated financial dashboard
- Open Finance sync (Pluggy)

Base: `/api/finance/`

### Legal finance workflows

- expenses with priority, installments, and payment control
- cases with payment structures
- fees and payroll
- reports and consolidations

Bases:

- `/api/expenses/`
- `/api/cases/`
- `/api/fees/`
- `/api/payroll/`
- `/api/reports/`
- `/api/other-income/`

Legacy aliases still available for compatibility:

- `/api/honorarios/`
- `/api/prolabore/`
- `/api/relatorios/`
- `/api/outras-entradas/`

### Product and feedback

- user-submitted suggestions
- automation and workflow support engine

Bases:

- `/api/suggestions/`
- `/api/motor/`

### API documentation

- Swagger: `/api/docs/`
- Redoc: `/api/redoc/`
- OpenAPI JSON: `/api/schema/`

## External integrations

### AbacatePay

Subscription checkout flow is already implemented in the backend, including checkout creation and a redirect URL for the frontend.

Technical guide:

- `docs/abacatepay-payment.md`

### Pluggy (Open Finance)

Connect token generation and account/transaction sync for balance and cash-flow consolidation.

## Modular architecture

Django apps in the codebase:

- `src/users`
- `src/firms`
- `src/expenses`
- `src/cases`
- `src/fees`
- `src/payroll`
- `src/other_income`
- `src/reports`
- `src/finance`
- `src/suggestions`
- `src/motor`

Central routing:

- `core/urls.py`

## Tech stack

- Python 3.12+
- Django 6
- Django REST Framework
- SimpleJWT
- drf-spectacular
- Poetry
- PostgreSQL (with configurable local fallback)

Key dependencies:

- `djangorestframework`
- `djangorestframework-simplejwt`
- `drf-spectacular`
- `python-decouple`
- `dj-database-url`
- `django-cors-headers`
- `requests`
- `posthog`

## Running locally

### 1) Prerequisites

- Python 3.12+
- Poetry

### 2) Install dependencies

```bash
poetry install
```

### 3) Configure environment

Create a `.env` file at the repository root with at least:

```env
SECRET_KEY="change-me"
DEBUG=True
DATABASE_URL="sqlite:///db.sqlite3"
```

To test financial integrations, also set:

```env
ABACATEPAY_API_KEY=""
ABACATEPAY_COMPLETION_URL=""
ABACATEPAY_RETURN_URL=""
PLUGGY_CLIENT_ID=""
PLUGGY_CLIENT_SECRET=""
```

### 4) Run migrations and start server

```bash
poetry run python manage.py migrate
poetry run python manage.py runserver 0.0.0.0:8000
```

Local API:

- `http://localhost:8000`

## Running with containers

### Docker

```bash
docker build -t fincecore .
docker run --env-file .env -p 8000:8000 fincecore
```

### Makefile (podman compose)

```bash
make build
make run
```

## Quick authentication example

### Register

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@fince.local",
    "password": "Password@2026",
    "full_name": "Dev Fince",
    "cpf": "111.222.333-44",
    "oab_number": "12345",
    "oab_state": "SP"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@fince.local",
    "password": "Password@2026"
  }'
```

## Quality and technical direction

This project is evolving quickly and we value contributions focused on:

- test coverage for critical workflows
- external integration resilience
- observability and telemetry
- tenant-aware security and authorization
- query and reporting performance

## Contribution and hiring

Contributing here is a practical way to work on a real Fince product.

We look for developers who demonstrate:

- technical ownership
- product and end-user focus
- high-quality delivery
- clear PR communication

How to contribute:

1. Fork the repository.
2. Create a branch (`feature/*`, `fix/*`, or `chore/*`).
3. Implement your improvement with technical context in commits.
4. Open a PR to `main` explaining problem, solution, and impact.
5. If possible, include tests and documentation updates.

If you want to contribute and also enter our hiring pipeline, submit consistent PRs and participate in technical discussions.

## Community and conduct

We want to grow as a startup without compromising respect, collaboration, and a safe contribution environment.

Read our code of conduct in `CODE_OF_CONDUCT.md` before participating in discussions, issues, and pull requests.

## Open source governance

Official project contribution, security, and policy documents:

- `CONTRIBUTING.md`
- `SECURITY.md`
- `GOVERNANCE.md`
- `COPYRIGHT.md`
- `TRADEMARKS.md`
- `DCO.md`
- `SUPPORT.md`

## Additional documentation

- `docs/users-api.md`
- `docs/finance-api.md`
- `docs/expenses-api.md`
- `docs/fees-api.md`
- `docs/reports-api.md`
- `docs/abacatepay-payment.md`

## License

Distributed under AGPLv3-or-later.

- Full text: `LICENSE`
- Community conduct: `CODE_OF_CONDUCT.md`
=======
# Desafio Técnico - Pokédex Analítica 🚀

Este repositório contém a solução para o desafio técnico de integração de dados com a PokeAPI.

## 📂 Estrutura do Projeto

* `pokemon_base.csv`: Lista inicial de Pokémons.
* `pokemon_completo.csv`: Arquivo final com dados consolidados e enriquecidos via PokeAPI.
* `respostas.txt`: Respostas para as perguntas de negócio do Time de Produto (incluindo o bônus).
* `dashboard.html`: Painel interativo gerado para visualização dinâmica dos dados.
* `main.py`: Script principal que realiza a extração, tratamento de erros, geração dos arquivos e cache local.

## ⚙️ Como Executar

1. Instale as dependências: `pip install requests`
2. Execute o script: `python main.py`
>>>>>>> 37bf79c06155bc6007958c258749d0b8fae94d9f
