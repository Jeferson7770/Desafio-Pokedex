import numpy as np
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum

class TaxationStrategy:
    def __init__(self, percentual_patronal, percentual_inss_socio=0.11, teto_inss_socio=908.85):
        self.percentual_patronal = percentual_patronal
        self.percentual_inss_socio = percentual_inss_socio
        self.teto_inss_socio = teto_inss_socio

    def calcular_cenario(self, valor_bruto):
        if valor_bruto == 0:
            return {
                "pro_labore_bruto": 0.0,
                "inss_socio": 0.0,
                "liquido_socio": 0.0,
                "inss_patronal": 0.0,
                "custo_total_escritorio": 0.0
            }
        
        inss_s = min(valor_bruto * self.percentual_inss_socio, self.teto_inss_socio)
        inss_p = valor_bruto * self.percentual_patronal
        return {
            "pro_labore_bruto": round(valor_bruto, 2),
            "inss_socio": round(inss_s, 2),
            "liquido_socio": round(valor_bruto - inss_s, 2),
            "inss_patronal": round(inss_p, 2),
            "custo_total_escritorio": round(valor_bruto + inss_p, 2)
        }


class SimplesNacionalAnexoIV(TaxationStrategy):
    def __init__(self):
        super().__init__(percentual_patronal=0.21)


class LucroPresumidoOuReal(TaxationStrategy):
    def __init__(self):
        super().__init__(percentual_patronal=0.268)


class AutonomoPessoaFisica(TaxationStrategy):
    def __init__(self):
        super().__init__(percentual_patronal=0.00)


class TaxationFactory:
    @staticmethod
    def obter_estrategia(tax_regime):
        mapeamento = {
            "SIMPLES": SimplesNacionalAnexoIV,
            "LUCRO_PRESUMIDO": LucroPresumidoOuReal,
            "LUCRO_REAL": LucroPresumidoOuReal
        }
        classe_tributaria = mapeamento.get(tax_regime, AutonomoPessoaFisica)
        return classe_tributaria()


class ProLaboreCalculator:
    SALARIO_MINIMO = 1518.00

    def __init__(self, receitas_lista, custo_fixo_medio, perfil, n_meses, rec_padrao):
        self.receitas_lista = receitas_lista
        self.custo_fixo_medio = custo_fixo_medio
        self.perfil = perfil
        self.n_meses = n_meses
        self.rec_padrao = rec_padrao
        self.faturamento_medio = sum(receitas_lista) / n_meses
        self.base_disponivel = max(0.0, self.faturamento_medio - custo_fixo_medio)

    def calcular_coeficiente_variacao(self):
        if self.faturamento_medio <= 0:
            return 0.0
        std_dev = np.std(self.receitas_lista) if len(self.receitas_lista) > 1 else 0.0
        return (std_dev / self.faturamento_medio) * 100

    def _aplicar_travas(self, valor_bruto):
        if self.base_disponivel <= 0:
            return 0.0
        if valor_bruto > (self.base_disponivel * 0.70):
            valor_bruto = self.base_disponivel * 0.70
        if valor_bruto < self.SALARIO_MINIMO and self.base_disponivel >= self.SALARIO_MINIMO:
            valor_bruto = self.SALARIO_MINIMO
        return valor_bruto

    def obter_valores_brutos_scenarios(self):
        meses_mais_fracos = sorted(self.receitas_lista)[:3]
        base_conservadora = max(0.0, (sum(meses_mais_fracos) / 3) - self.custo_fixo_medio)
        
        bruto_cons = self._aplicar_travas(base_conservadora * 0.30)
        bruto_equi = self._aplicar_travas(self.base_disponivel * 0.425)
        bruto_maximo = self._aplicar_travas(self.base_disponivel * 0.575)
        
        return bruto_cons, bruto_equi, bruto_maximo

    def gerar_mensagem_alerta(self):
        if self.base_disponivel < self.SALARIO_MINIMO:
            return "Sua base disponível atual não suporta um pró-labore dentro do mínimo recomendado. Isso pode indicar que os custos fixos estão altos em relação à receita."
        return None


class ProLaboreServicePipeline:
    def __init__(self, transactions_queryset):
        self.queryset = transactions_queryset

    def _identificar_perfil_e_periodo(self, user):
        primeira_tx = self.queryset.filter(account__firm__members__user=user).order_by('date').first()
        if not primeira_tx:
            return "INICIANTE", 3, "Conservador"
        
        dias = (timezone.localdate() - primeira_tx.date).days
        meses = dias // 30

        if meses < 6:
            return "INICIANTE", 3, "Conservador"
        elif 6 <= meses <= 24:
            return "INTERMEDIARIO", 6, "Equilibrado"
        return "AVANCADO", 12, "Máximo seguro"

    def processar(self, user, tax_regime):
        perfil, n_meses, rec_padrao = self._identificar_perfil_e_periodo(user)
        data_limite = timezone.localdate() - timedelta(days=n_meses * 30)
        
        base_tx = self.queryset.filter(
            account__firm__members__user=user,
            date__gte=data_limite
        )

        receitas_tx = base_tx.filter(transaction_type="INFLOW")
        if perfil in ["INICIANTE", "INTERMEDIARIO"]:
            receitas_tx = receitas_tx.exclude(description__icontains="exito")

        receitas_mes = (
            receitas_tx.values('date__month')
            .annotate(total=Sum('amount'))
            .values_list('total', flat=True)
        )
        
        receitas_lista = [float(r) for r in receitas_mes] or [0.0]
        while len(receitas_lista) < n_meses:
            receitas_lista.append(0.0)

        custo_tot = base_tx.filter(transaction_type="OUTFLOW").aggregate(total=Sum('amount'))['total'] or 0
        custo_fixo_medio = float(custo_tot) / n_meses

        calculadora = ProLaboreCalculator(receitas_lista, custo_fixo_medio, perfil, n_meses, rec_padrao)
        estrategia_fiscal = TaxationFactory.obtain_strategy(tax_regime)

        bruto_cons, bruto_equi, bruto_max = calculadora.obtain_gross_values_scenarios()

        return {
            "base_disponivel": round(calculadora.base_disponivel, 2),
            "coef_variacao": round(calculadora.calcular_coeficiente_variacao(), 1),
            "meses_analisados": n_meses,
            "nivel_recomendado": rec_padrao,
            "mensagem_alerta": calculadora.gerar_mensagem_alerta(),
            "conservador": estrategia_fiscal.calcular_cenario(bruto_cons),
            "equilibrado": estrategia_fiscal.calcular_cenario(bruto_equi),
            "maximo_seguro": estrategia_fiscal.calcular_cenario(bruto_max)
        }


def calcular_pro_labore_escritorio(user, transactions_queryset, tax_regime):
    pipeline = ProLaboreServicePipeline(transactions_queryset)
    return pipeline.processar(user, tax_regime)