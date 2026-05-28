from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
import datetime

from ..models.motor import SimulacaoPrioridade
from ..serializers.motor import SimulacaoPrioridadeSerializer, SalvarConfiguracaoQuerySerializer
from ..utils.calculo_prioridade import MotorPrioridadeEngine

class MotorPrioridadeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SimulacaoPrioridadeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_firm(self, user):
        membership = user.firm_memberships.first()
        if not membership:
            raise ValidationError("O usuário não possui empresa vinculada.")
        return membership.firm

    def get_queryset(self):
        firm = self._get_user_firm(self.request.user)
        queryset = SimulacaoPrioridade.objects.filter(firm=firm).prefetch_related('items__parcela__expense')
        
        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")
        
        if year and month:
            try:
                queryset = queryset.filter(
                    reference_date__year=int(year),
                    reference_date__month=int(month)
                )
            except ValueError:
                pass
                
        return queryset

    @action(detail=False, methods=["post"], url_path="salvar-configuracao")
    def salvar_configuracao(self, request):
        """
        Executa o motor de prioridade, salva o estado atualizado no banco de dados 
        e retorna a configuração limpa diretamente pro Frontend.
        """
        serializer = SalvarConfiguracaoQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ano = serializer.validated_data["year"]
        mes = serializer.validated_data["month"]
        firm = self._get_user_firm(request.user)
        
        engine = MotorPrioridadeEngine(firm=firm)
        simulacao_persistida = engine.calcular_e_salvar(ano=ano, mes=mes)
        
        response_serializer = self.get_serializer(simulacao_persistida)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)