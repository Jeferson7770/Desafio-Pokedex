from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from ..models.motor import SimulacaoPrioridade
from ..serializers.motor import SimulacaoPrioridadeSerializer
from ..utils.calculo_prioridade import MotorPrioridadeEngine
from ...users.utils.telemetry import track_event
from ...users.utils.firm_mixin import FirmMixin
from ...firms.models.firm_structure import Firm


class MotorPrioridadeViewSet(FirmMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = SimulacaoPrioridadeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_firm_object(self):
        firm_id = self._get_firm_id()
        if not firm_id:
            raise ValidationError("O usuário não possui empresa vinculada.")
        return Firm.objects.get(pk=firm_id)

    def list(self, request, *args, **kwargs):
        """GET /api/motor/ (Cálculo dinâmico padrão inicial)"""
        firm = self._get_firm_object()
        hoje = timezone.localdate()
        
        engine = MotorPrioridadeEngine(firm=firm)
        dados_calculados = engine.calcular_dinamico(ano=hoje.year, mes=hoje.month)
        
        track_event(
            user=request.user,
            event_name="motor_prioridade_calculado_dinamico",
            properties={
                "ano_referencia": hoje.year,
                "mes_referencia": hoje.month,
                "total_itens_retornados": len(dados_calculados.get("pagamentos_recomendados", [])) + len(dados_calculados.get("pagamentos_nao_cobertos", []))
            }
        )
        
        return Response(dados_calculados, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="salvar-configuracao")
    def salvar_configuracao(self, request):
        """
        POST /api/motor/salvar-configuracao/
        Lê o array ordenado enviado pelo frontend e salva no banco mantendo essa ordem exata.
        """
        firm = self._get_firm_object()
        hoje = timezone.localdate()

        recomendados = request.data.get("pagamentos_recomendados", [])
        nao_cobertos = request.data.get("pagamentos_nao_cobertos", [])
        itens_da_tela = recomendados + nao_cobertos

        if not itens_da_tela:
            track_event(
                user=request.user,
                event_name="motor_prioridade_salvar_falha",
                properties={"motivo_erro": "payload_vazio"}
            )
            raise ValidationError("O payload enviado está vazio ou não possui a chave 'pagamentos_recomendados'.")

        engine = MotorPrioridadeEngine(firm=firm)
        simulacao_persistida = engine.salvar_configuracao_da_tela(
            ano=hoje.year, 
            mes=hoje.month, 
            itens_da_tela=itens_da_tela
        )
        
        track_event(
            user=request.user,
            event_name="motor_prioridade_configuracao_salva",
            properties={
                "simulation_id": simulacao_persistida.id if hasattr(simulacao_persistida, 'id') else None,
                "ano_referencia": hoje.year,
                "mes_referencia": hoje.month,
                "recomendados_count": len(recomendados),
                "nao_cobertos_count": len(nao_cobertos),
                "total_itens_priorizados": len(itens_da_tela)
            }
        )
        
        response_serializer = self.get_serializer(simulacao_persistida)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)