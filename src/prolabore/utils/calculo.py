import numpy as np
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from ...dinheiro.models.dinheiro import Transaction

def calcular_pro_labore_escritorio(user, estagio, tax_regime):
    meses_mapeamento = {"INICIANTE": 6, "INTERMEDIARIO": 12, "AVANCADO": 24}
    meses_para_analisar = meses_mapeamento.get(estagio, 6)

    hoje = timezone.localdate()
    data_limite = hoje - timedelta(days=meses_para_analisar * 30)
    
    receitas_query = (
        Transaction.objects.filter(
            account__firm__members__user=user,
            transaction_type="INFLOW",
            date__gte=data_limite
        )
        .values('date__month')
        .annotate(total=Sum('amount'))
        .values_list('total', flat=True)
    )
    
    receitas_lista = [float(r) for r in receitas_query] or [0.0]
    while len(receitas_lista) < meses_para_analisar:
        receitas_lista.append(0.0)

    faturamento_medio = sum(receitas_lista) / len(receitas_lista)

    custo_total = Transaction.objects.filter(
        account__firm__members__user=user,
        transaction_type="OUTFLOW",
        date__gte=data_limite
    ).aggregate(total=Sum('amount'))['total'] or 0
    custo_fixo_medio = float(custo_total) / meses_para_analisar

    base_disponivel = max(0.0, faturamento_medio - custo_fixo_medio)
    std_dev = np.std(receitas_lista) if len(receitas_lista) > 1 else 0.0
    coef_variacao = (std_dev / faturamento_medio) * 100 if faturamento_medio > 0 else 0.0

    SALARIO_MINIMO = 1518.00
    mensagem_alerta = None
    if base_disponivel < SALARIO_MINIMO:
        mensagem_alerta = f"A base disponível não comporta pró-labore acima do salário mínimo (R$ {SALARIO_MINIMO:,.2f})."

    percentual_patronal = 0.20 if tax_regime in ["SIMPLES", "LUCRO_PRESUMIDO"] else 0.00
    percentual_inss_socio = 0.11

    bruto_maximo = max(SALARIO_MINIMO, base_disponivel * 0.7) if base_disponivel > SALARIO_MINIMO else SALARIO_MINIMO
    bruto_equi = max(SALARIO_MINIMO, base_disponivel * 0.5) if base_disponivel > SALARIO_MINIMO else SALARIO_MINIMO
    bruto_cons = max(SALARIO_MINIMO, base_disponivel * 0.3) if base_disponivel > SALARIO_MINIMO else SALARIO_MINIMO

    def gerar_cenario(valor_bruto):
        inss_s = round(valor_bruto * percentual_inss_socio, 2)
        inss_p = round(valor_bruto * percentual_patronal, 2)
        return {
            "pro_labore_bruto": round(valor_bruto, 2),
            "inss_socio": inss_s,
            "liquido_socio": round(valor_bruto - inss_s, 2),
            "inss_patronal": inss_p,
            "custo_total_escritorio": round(valor_bruto + inss_p, 2)
        }

    return {
        "base_disponivel": round(base_disponivel, 2),
        "coef_variacao": round(coef_variacao, 1),
        "meses_analisados": len([r for r in receitas_query if r > 0]) or 1,
        "nivel_recomendado": "Máximo Seguro" if coef_variacao < 15 else "Conservador",
        "mensagem_alerta": mensagem_alerta,
        "conservador": gerar_cenario(bruto_cons),
        "equilibrado": gerar_cenario(bruto_equi),
        "maximo_seguro": gerar_cenario(bruto_maximo)
    }