from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import models
from datetime import datetime, timedelta
from ..models.relatorios import FinancialReportSummary
from ..serializers.relatorios import FinancialReportDashboardSerializer

class FinancialReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = FinancialReportSummary.objects.all()
    serializer_class = FinancialReportDashboardSerializer

    def _get_user_firm(self, user):
        """
        Busca a firma do usuário através do relacionamento de memberships,
        idêntico ao funcionamento dos honorários.
        """
        membership = user.firm_memberships.first()
        if not membership:
            raise ValidationError(
                {"detail": "O usuário autenticado não possui uma empresa/firma vinculada ao seu perfil."}
            )
        return membership.firm

    def get_queryset(self):
        return self.queryset.filter(firm__members__user=self.request.user)

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data'), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        filters = self._resolve_date_filters(request)
        queryset = self.get_queryset().filter(filters)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = self.request.user
        firm = self._get_user_firm(user)
        
        if getattr(serializer, 'is_bulk', False):
            for item in serializer.validated_data:
                item['firm'] = firm
            serializer.save()
        else:
            serializer.save(firm=firm)

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