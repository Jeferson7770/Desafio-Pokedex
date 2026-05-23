from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from ..models.relatorios import FinancialReportSummary
from ..serializers.relatorios import FinancialReportDashboardSerializer

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
        """
        firm = self._get_user_firm(request.user)
        
        now = timezone.now()
        year = request.query_params.get('year', str(now.year))
        month = request.query_params.get('month', str(now.month))

        try:
            report_instance = self.get_queryset().get(firm=firm, year=year, month=month)
        except FinancialReportSummary.DoesNotExist:
            return Response(
                {"detail": f"Nenhum relatório consolidado encontrado para o período {month}/{year}."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(report_instance)
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

        response_serializer = self.get_serializer(instance)
        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )