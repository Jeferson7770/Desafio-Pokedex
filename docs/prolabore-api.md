# Guia de uso da API de Pro-Labore

Este documento descreve como consumir o endpoint de calculo e simulacao de pro-labore.

## 1. Autenticacao

```http
Authorization: Bearer <seu_token>
Content-Type: application/json
```

Base URL:

```text
/api/pro-labore/
```

## 2. O que e o Pro-Labore

O endpoint de pro-labore calcula, com base no historico financeiro do advogado e seu regime tributario, tres cenarios de retirada mensal:

- **conservador**: retirada minima segura.
- **equilibrado**: retirada balanceada.
- **maximo_seguro**: retirada maxima sem comprometer o caixa.

Cada cenario inclui: valor bruto, INSS do socio, liquido para o socio, INSS patronal e custo total para o escritorio.

O resultado e calculado e salvo automaticamente no historico de simulacoes.

## 3. Calcular pro-labore

```http
POST /api/pro-labore/
```

Nao requer body. O backend usa:
- O perfil do advogado autenticado (`tax_regime`).
- O historico de transacoes da conta bancaria.

Resposta `200`:

```json
{
  "base_disponivel": 15800.0,
  "coef_variacao": 0.22,
  "meses_analisados": 6,
  "nivel_recomendado": "INTERMEDIARIO",
  "mensagem_alerta": null,
  "conservador": {
    "pro_labore_bruto": 3500.0,
    "inss_socio": 385.0,
    "liquido_socio": 3115.0,
    "inss_patronal": 770.0,
    "custo_total_escritorio": 4270.0
  },
  "equilibrado": {
    "pro_labore_bruto": 5200.0,
    "inss_socio": 572.0,
    "liquido_socio": 4628.0,
    "inss_patronal": 1144.0,
    "custo_total_escritorio": 6344.0
  },
  "maximo_seguro": {
    "pro_labore_bruto": 7900.0,
    "inss_socio": 869.0,
    "liquido_socio": 7031.0,
    "inss_patronal": 1738.0,
    "custo_total_escritorio": 9638.0
  }
}
```

Campos:

| Campo | Descricao |
|-------|-----------|
| `base_disponivel` | Receita disponivel media calculada pelo engine |
| `coef_variacao` | Coeficiente de variacao da renda (0 a 1) |
| `meses_analisados` | Quantos meses de historico foram usados |
| `nivel_recomendado` | `INICIANTE`, `INTERMEDIARIO` ou `AVANCADO` |
| `mensagem_alerta` | Texto de alerta quando renda e muito variavel ou historico curto (pode ser null) |

## 4. Listar historico de simulacoes

```http
GET /api/pro-labore/
```

Retorna todas as simulacoes salvas do usuario autenticado, ordenadas da mais recente.

Resposta `200`:

```json
[
  {
    "id": 1,
    "perfil_estagio": "INTERMEDIARIO",
    "base_disponivel": "15800.00",
    "coef_variacao": "0.22",
    "meses_analisados": 6,
    "pro_labore_sugerido": "7900.00",
    "custo_total_escritorio": "9638.00",
    "created_at": "2026-06-04T10:00:00Z"
  }
]
```

## 5. Perfis de estagio

| Valor | Descricao |
|-------|-----------|
| `INICIANTE` | Variabilidade alta ou historico curto — retirada conservadora recomendada |
| `INTERMEDIARIO` | Variabilidade media — equilibrio entre seguranca e retorno |
| `AVANCADO` | Renda estavel e historico longo — pode optar pelo maximo seguro |

## 6. Pre-requisitos

- Usuario deve ter um `LawyerProfile` com `tax_regime` definido.
- O backend usa o regime tributario para calcular INSS e encargos.
- Sem perfil de advogado, retorna `404`.

## 7. Checklist rapido para o frontend

1. Chamar `POST /api/pro-labore/` para calcular — sem body.
2. Exibir os tres cenarios ao usuario para ele escolher qual retirar.
3. `mensagem_alerta` deve ser exibido prominentemente quando nao for null (avisa sobre renda instavel).
4. `GET /api/pro-labore/` para exibir historico de calculos anteriores.
