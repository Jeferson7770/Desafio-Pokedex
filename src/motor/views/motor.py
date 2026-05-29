from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from ..models.motor import SimulacaoPrioridade
from ..serializers.motor import SimulacaoPrioridadeSerializer
from ..utils.calculo_prioridade import MotorPrioridadeEngine

class MotorPrioridadeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SimulacaoPrioridadeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_firm(self, user):
        membership = user.firm_memberships.first()
        if not membership:
            raise ValidationError("O usuário não possui empresa vinculada.")
        return membership.firm

    def list(self, request, *args, **kwargs):
        """GET /api/motor/ (Cálculo dinâmico padrão inicial)"""
        firm = self._get_user_firm(request.user)
        hoje = timezone.localdate()
        
        engine = MotorPrioridadeEngine(firm=firm)
        dados_calculados = engine.calcular_dinamico(ano=hoje.year, mes=hoje.month)
        
        return Response(dados_calculados, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="salvar-configuracao")
    def salvar_configuracao(self, request):
        """
        POST /api/motor/salvar-configuracao/
        Lê o array ordenado enviado pelo frontend e salva no banco mantendo essa ordem exata.
        """
        firm = self._get_user_firm(request.user)
        hoje = timezone.localdate()
        
        recomendados = request.data.get("pagamentos_recomendados", [])
        nao_cobertos = request.data.get("pagamentos_nao_cobertos", [])
        itens_da_tela = recomendados + nao_cobertos

        if not itens_da_tela:
            raise ValidationError("O payload enviado está vazio ou não possui a chave 'pagamentos_recomendados'.")

        engine = MotorPrioridadeEngine(firm=firm)
        simulacao_persistida = engine.salvar_configuracao_da_tela(
            ano=hoje.year, 
            mes=hoje.month, 
            itens_da_tela=itens_da_tela
        )
        
        response_serializer = self.get_serializer(simulacao_persistida)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)