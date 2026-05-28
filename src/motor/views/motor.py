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
        """
        GET /api/motor/
        Executa o cálculo do motor em tempo real com base no mês e ano atuais
        e entrega diretamente para o frontend renderizar.
        """
        firm = self._get_user_firm(request.user)
        
        hoje = timezone.localdate()
        ano = hoje.year
        mes = hoje.month

        engine = MotorPrioridadeEngine(firm=firm)
        
        dados_calculados = engine.calcular_dinamico(ano=ano, mes=mes)
        
        return Response(dados_calculados, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="salvar-configuracao")
    def salvar_configuracao(self, request):
        """
        POST /api/motor/salvar-configuracao/ (Sem body)
        Executa o motor, persiste a foto atual do mês vigente no banco de dados
        e retorna os dados persistidos.
        """
        firm = self._get_user_firm(request.user)
        
        hoje = timezone.localdate()
        ano = hoje.year
        mes = hoje.month

        engine = MotorPrioridadeEngine(firm=firm)
        simulacao_persistida = engine.calcular_e_salvar(ano=ano, mes=mes)
        
        response_serializer = self.get_serializer(simulacao_persistida)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)