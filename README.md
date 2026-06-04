# fincecore

Backend oficial da Fince: uma plataforma de gestao financeira para advogados e escritorios de advocacia.

Somos uma empresa privada e operamos este produto em ambiente real. Este repositorio e open source porque acreditamos em construcao publica com padrao de producao.

Queremos atrair devs que curtam resolver problemas reais de produto B2B financeiro. Contribuidores consistentes entram no nosso radar para contratacao.

## O que o projeto resolve

FinceCore centraliza o motor de negocio para:

- organizacao financeira de escritorios juridicos
- controle de despesas, honorarios e outras entradas
- acompanhamento de fluxo de caixa e indicadores
- estrutura multi-escritorio com permissao por membro
- integracao com provedores externos de dados financeiros e pagamento

## Principais capacidades da API

### Autenticacao e conta

- JWT com login por email
- onboarding de perfil juridico
- gerenciamento de dispositivos e seguranca de conta

Base: `/api/auth/`

### Escritorios e membros

- criacao de escritorio
- convite/adicao de membros
- isolamento de dados por escritorio

Base: `/api/firms/`

### Financeiro operacional

- contas bancarias e transacoes
- dashboard financeiro consolidado
- sincronizacao com Open Finance (Pluggy)

Base: `/api/dinheiro/`

### Gestao financeira juridica

- despesas com prioridade, parcelamento e controle de pagamento
- casos com estrutura de recebimento
- honorarios e pro-labore
- relatorios e consolidacoes

Bases:

- `/api/expenses/`
- `/api/cases/`
- `/api/honorarios/`
- `/api/prolabore/`
- `/api/relatorios/`
- `/api/outras-entradas/`

### Produto e feedback

- sugestoes enviadas pelos usuarios
- automacoes e motor de apoio a fluxos

Bases:

- `/api/suggestions/`
- `/api/motor/`

### Documentacao de API

- Swagger: `/api/docs/`
- Redoc: `/api/redoc/`
- OpenAPI JSON: `/api/schema/`

## Integracoes externas

### AbacatePay

Fluxo de checkout de assinatura ja implementado no backend, com criacao de checkout e retorno de URL para redirecionamento no frontend.

Guia tecnico dedicado:

- `docs/abacatepay-pagamento.md`

### Pluggy (Open Finance)

Geracao de connect token e sincronizacao de contas/transacoes para consolidar saldos e fluxo.

## Arquitetura em modulos

Apps Django no codigo:

- `src/users`
- `src/firms`
- `src/expenses`
- `src/cases`
- `src/honorarios`
- `src/prolabore`
- `src/outras_entradas`
- `src/relatorios`
- `src/dinheiro`
- `src/suggestions`
- `src/motor`

Roteamento central:

- `core/urls.py`

## Stack tecnica

- Python 3.12+
- Django 6
- Django REST Framework
- SimpleJWT
- drf-spectacular
- Poetry
- PostgreSQL (com fallback local configuravel)

Dependencias principais no projeto:

- `djangorestframework`
- `djangorestframework-simplejwt`
- `drf-spectacular`
- `python-decouple`
- `dj-database-url`
- `django-cors-headers`
- `requests`
- `posthog`

## Como rodar localmente

### 1) Pre-requisitos

- Python 3.12+
- Poetry

### 2) Instalar dependencias

```bash
poetry install
```

### 3) Configurar ambiente

Crie um arquivo `.env` na raiz com o minimo:

```env
SECRET_KEY="change-me"
DEBUG=True
DATABASE_URL="sqlite:///db.sqlite3"
```

Para testar integracoes financeiras, configure tambem:

```env
ABACATEPAY_API_KEY=""
ABACATEPAY_COMPLETION_URL=""
ABACATEPAY_RETURN_URL=""
PLUGGY_CLIENT_ID=""
PLUGGY_CLIENT_SECRET=""
```

### 4) Migrar banco e subir servidor

```bash
poetry run python manage.py migrate
poetry run python manage.py runserver 0.0.0.0:8000
```

API local:

- `http://localhost:8000`

## Execucao com container

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

## Exemplo rapido de autenticacao

### Registro

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

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@fince.local",
    "password": "Senha@2026"
  }'
```

## Qualidade e direcao tecnica

Este projeto esta evoluindo rapido e valorizamos contribuicoes com foco em:

- cobertura de testes para fluxos criticos
- resiliencia de integracoes externas
- observabilidade e telemetria
- seguranca e autorizacao por tenant
- performance de consultas e relatorios

## Contribuicao e contratacao

Contribuir aqui e uma forma pratica de trabalhar em um produto real da Fince.

Buscamos devs que demonstrem:

- ownership tecnico
- preocupacao com produto e usuario final
- capacidade de entrega com qualidade
- comunicacao clara em PRs

Como contribuir:

1. Faça fork do repositorio.
2. Crie uma branch (`feature/*`, `fix/*` ou `chore/*`).
3. Implemente sua melhoria com contexto tecnico no commit.
4. Abra PR para `main` explicando problema, solucao e impacto.
5. Se possivel, inclua teste e atualizacao da documentacao.

Se voce quer contribuir e tambem entrar no nosso pipeline de contratacao, abra PRs consistentes e participe das discussoes tecnicas.

## Documentacao adicional

- `docs/users-api.md`
- `docs/dinheiro-api.md`
- `docs/expenses-api.md`
- `docs/honorarios-api.md`
- `docs/relatorios-api.md`
- `docs/abacatepay-pagamento.md`

## Licenca

Consulte o arquivo de licenca do repositorio para os termos de uso.
