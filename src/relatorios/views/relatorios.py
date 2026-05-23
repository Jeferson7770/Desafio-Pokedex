from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from datetime import datetime, timedelta
from ..models.relatorios import FinancialReportSummary
from ..serializers.relatorios import FinancialReportDashboardSerializer

class FinancialReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = FinancialReportSummary.objects.all()

    def get_queryset(self):
        return self.queryset.filter(profile__user=self.request.user)

    def _resolve_date_filters(self, request) -> models.Q:
        period = request.query_params.get('period', 'semester')
        start_date_param = request.query_params.get('start_date')
        end_date_param = request.query_params.get('end_date')

        if start_date_param and end_date_param:
            start_year, start_month = map(int, start_date_param.split('-'))
            end_year, end_month = map(int, end_date_param.split('-'))
            return (
                models.Q(year__gt=start_year) | models.Q(year=start_year, month__gte=start_month)
            ) & (
                models.Q(year__lt=end_year) | models.Q(year=end_year, month__lte=end_month)
            )

        period_map = {'month': 1, 'trimester': 3, 'semester': 6, 'year': 12}
        months_to_subtract = period_map.get(period, 6)
        
        today = datetime.now()
        q_objects = models.Q()
        for i in range(months_to_subtract):
            check_date = today - timedelta(days=i*30)
            q_objects |= models.Q(month=check_date.month, year=check_date.year)
        return q_objects

    def list(self, request, *args, **kwargs):
        filters = self._resolve_date_filters(request)
        queryset = self.get_queryset().filter(filters)

        if not queryset.exists():
            return Response(
                {"detail": "Nenhum dado processado para este intervalo."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = FinancialReportDashboardSerializer(queryset)
        return Response(serializer.data)