from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from ..models.relatorios import FinancialReportSummary
from ..serializers.relatorios import FinancialReportDashboardSerializer
from ...users.utils.telemetry import track_event


class FinancialReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = FinancialReportSummary.objects.all()
    serializer_class = FinancialReportDashboardSerializer

    def _get_user_firm(self, user):
        """
        Busca a firma do usuário através do relacionamento de memberships.
        """
        membership = user.firm_memberships.first()
        if not membership:
            raise ValidationError(
                {"detail": "O usuário autenticado não possui uma empresa/firma vinculada ao seu perfil."}
            )
        return membership.firm

    def get_queryset(self):
        return self.queryset.filter(firm__members__user=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        Sobrescreve o list tradicional para retornar o payload único do relatório 
        com base nos filtros de ano e mês (?year=2026&month=05).
        Retorna status 200 mesmo se não houver dados no banco para o período.
        """
        firm = self._get_user_firm(request.user)
        
        now = timezone.now()
        
        try:
            year = int(request.query_params.get('year', now.year))
            month = int(request.query_params.get('month', now.month))
        except ValueError:
            track_event(
                user=request.user,
                event_name="relatorio_financeiro_filtro_erro",
                properties={"motivo_erro": "ano_ou_mes_invalido"}
            )
            raise ValidationError({"detail": "Os parâmetros 'year' e 'month' devem ser inteiros válidos."})

        try:
            report_instance = self.get_queryset().get(firm=firm, year=year, month=month)
            dados_existiam = True
        except FinancialReportSummary.DoesNotExist:
            report_instance = FinancialReportSummary(
                firm=firm,
                year=year,
                month=month,
                total_revenue=0.00,
                total_expense=0.00
            )
            dados_existiam = False

        serializer = self.get_serializer(report_instance)

        track_event(
            user=request.user,
            event_name="relatorio_financeiro_visualizado",
            properties={
                "ano_relatorio": year,
                "mes_relatorio": month,
                "continha_dados_consolidados": dados_existiam,
                "total_revenue_snapshot": float(report_instance.total_revenue),
                "total_expense_snapshot": float(report_instance.total_expense)
            }
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """
        Garante o comportamento de atualizar ou criar (Upsert) baseado em firma/ano/mês,
        evitando duplicatas indesejadas no banco de dados.
        """
        user = request.user
        firm = self._get_user_firm(user)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        year = serializer.validated_data.get('year')
        month = serializer.validated_data.get('month')

        instance, created = FinancialReportSummary.objects.update_or_create(
            firm=firm,
            year=year,
            month=month,
            defaults=serializer.validated_data
        )

        track_event(
            user=user,
            event_name="relatorio_financeiro_consolidado",
            properties={
                "report_id": instance.id if instance.id else None,
                "ano_relatorio": year,
                "mes_relatorio": month,
                "acao": "criado" if created else "atualizado",
                "total_revenue": float(instance.total_revenue),
                "total_expense": float(instance.total_expense)
            }
        )

        response_serializer = self.get_serializer(instance)
        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )