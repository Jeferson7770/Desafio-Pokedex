from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from ..models.relatorios import FinancialReportSummary
from ..serializers.relatorios import FinancialReportDashboardSerializer
from ...users.utils.telemetry import track_event
from ...users.utils.firm_mixin import FirmMixin


class FinancialReportViewSet(FirmMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = FinancialReportSummary.objects.all()
    serializer_class = FinancialReportDashboardSerializer

    def get_queryset(self):
        firm_id = self._get_firm_id()
        if not firm_id:
            return self.queryset.none()
        return self.queryset.filter(firm_id=firm_id)

    def list(self, request, *args, **kwargs):
        """
        Sobrescreve o list tradicional para retornar o payload único do relatório 
        com base nos filtros de ano e mês (?year=2026&month=05).
        Retorna status 200 mesmo se não houver dados no banco para o período.
        """
        firm_id = self._get_firm_id()
        if not firm_id:
            raise ValidationError({"detail": "O usuário autenticado não possui uma empresa/firma vinculada ao seu perfil."})

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

        cache_key = f"financial_report:{firm_id}:{year}:{month}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        try:
            report_instance = self.get_queryset().get(firm_id=firm_id, year=year, month=month)
            dados_existiam = True
        except FinancialReportSummary.DoesNotExist:
            report_instance = FinancialReportSummary(
                firm_id=firm_id,
                year=year,
                month=month,
                total_revenue=0.00,
                total_expense=0.00
            )
            dados_existiam = False

        serializer = self.get_serializer(report_instance)
        cache.set(cache_key, serializer.data, timeout=300)

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
        firm_id = self._get_firm_id()
        if not firm_id:
            raise ValidationError({"detail": "O usuário autenticado não possui uma empresa/firma vinculada ao seu perfil."})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        year = serializer.validated_data.get('year')
        month = serializer.validated_data.get('month')

        instance, created = FinancialReportSummary.objects.update_or_create(
            firm_id=firm_id,
            year=year,
            month=month,
            defaults=serializer.validated_data,
        )
        cache.delete(f"financial_report:{firm_id}:{year}:{month}")

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