# Crie ou adicione em seu arquivo de views/viewsets correspondente ao módulo financeiro/dashboard
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Q
from django.utils import timezone
import datetime

from ...honorarios.models.honorarios import ParcelaHonorario
from ...expenses.models.expenses import ParcelaDespesa
from ..models.dinheiro import BankAccount


class FinanceDashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_user_firm(self, user):
        membership = user.firm_memberships.first()
        if not membership:
            return None
        return membership.firm

    def get(self, request):
        user = request.user
        firm = self._get_user_firm(user)
        
        if not firm:
            return Response(
                {"detail": "Usuário não vinculado a nenhuma empresa."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        hoje = timezone.localdate()
        try:
            year = int(request.query_params.get("year", hoje.year))
            month = int(request.query_params.get("month", hoje.month))
        except ValueError:
            return Response(
                {"detail": "Parâmetros 'year' e 'month' precisam ser inteiros válidos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        entradas_mes = ParcelaHonorario.objects.filter(
            honorario__firm=firm,
            due_date__year=year,
            due_date__month=month,
            status="RECEBIDO"
        ).aggregate(total=Sum("amount"))["total"] or 0.0

        a_receber = ParcelaHonorario.objects.filter(
            honorario__firm=firm,
            due_date__year=year,
            due_date__month=month,
            status="PENDENTE"
        ).aggregate(total=Sum("amount"))["total"] or 0.0

        saidas_mes = ParcelaDespesa.objects.filter(
            expense__firm=firm,
            expense__is_active=True,
            due_date__year=year,
            due_date__month=month,
            is_paid=False
        ).aggregate(total=Sum("amount"))["total"] or 0.0

        saldo_liquido = float(entradas_mes) - float(saidas_mes)

        saldo_em_conta = BankAccount.objects.filter(
            firm=firm
        ).aggregate(total=Sum("current_balance"))["total"] or 0.0

        return Response({
            "ano_referencia": year,
            "mes_referencia": month,
            "entradas_do_mes": float(entradas_mes),
            "a_receber": float(a_receber),
            "saidas_do_mes": float(saidas_mes),
            "saldo_liquido": float(saldo_liquido),
            "saldo_em_conta": float(saldo_em_conta)
        }, status=status.HTTP_200_OK)