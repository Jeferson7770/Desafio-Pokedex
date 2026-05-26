from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction

from ..models.prolabore import ProLaboreSimulation
from ..serializers.prolabore import (
    ProLaboreCalculoSerializer, 
    ProLaboreSimulationSerializer
)
from ...dinheiro.models.dinheiro import Transaction
from ..utils.calculo import calcular_pro_labore_escritorio


class ProLaboreViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProLaboreSimulationSerializer

    def get_queryset(self):
        return ProLaboreSimulation.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user
        profile = getattr(user, "profile", None)
        
        if not profile:
            return Response(
                {"detail": "Perfil de advogado não encontrado para realizar o cálculo."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Dispara o cálculo usando as movimentações totais históricas da firma do usuário
        all_transactions = Transaction.objects.all()
        
        calculos_objeto = calcular_pro_labore_escritorio(
            user=user, 
            transactions_queryset=all_transactions, 
            tax_regime=profile.tax_regime
        )

        with db_transaction.atomic():
            ProLaboreSimulation.objects.create(
                user=user,
                perfil_estagio=calculos_objeto["nivel_recomendado"].upper(),
                base_disponivel=calculos_objeto["base_disponivel"],
                coef_variacao=calculos_objeto["coef_variacao"],
                meses_analisados=calculos_objeto["meses_analisados"],
                pro_labore_sugerido=calculos_objeto["maximo_seguro"]["pro_labore_bruto"],
                custo_total_escritorio=calculos_objeto["maximo_seguro"]["custo_total_escritorio"]
            )

        output_serializer = ProLaboreCalculoSerializer(data=calculos_objeto)
        output_serializer.is_valid(raise_exception=True)
        return Response(output_serializer.data, status=status.HTTP_200_OK)