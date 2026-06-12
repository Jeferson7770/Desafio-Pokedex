import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from ..models.honorarios import Honorario, ParcelaHonorario
from ..serializers.honorarios import HonorarioSerializer, ParcelaHonorarioSerializer
from django.core.cache import cache
from ...users.utils.telemetry import track_event
from ...users.utils.firm_mixin import FirmMixin
from ...users.utils.cache_utils import invalidar_cache_financeiro


class HonorarioViewSet(FirmMixin, viewsets.ModelViewSet):
    serializer_class = HonorarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        firm_id = self._get_firm_id()
        if not firm_id:
            raise ValidationError("O usuário não está vinculado a nenhuma empresa (firm).")
        queryset = Honorario.objects.filter(firm_id=firm_id)

        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date and end_date:
            try:
                start = datetime.date.fromisoformat(start_date)
                end = datetime.date.fromisoformat(end_date)
            except ValueError:
                raise ValidationError("Os parâmetros 'start_date' e 'end_date' devem estar no formato YYYY-MM-DD.")
            queryset = queryset.filter(
                installments__due_date__gte=start,
                installments__due_date__lte=end,
            ).distinct()
        elif year and month:
            try:
                year_int, month_int = int(year), int(month)
            except ValueError:
                raise ValidationError("Os parâmetros 'year' e 'month' devem ser inteiros válidos.")
            start = datetime.date(year_int, month_int, 1)
            end = datetime.date(year_int, month_int + 1, 1) if month_int < 12 else datetime.date(year_int + 1, 1, 1)
            queryset = queryset.filter(
                installments__due_date__gte=start,
                installments__due_date__lt=end,
            ).distinct()
        elif year:
            try:
                year_int = int(year)
            except ValueError:
                raise ValidationError("O parâmetro 'year' deve ser um número inteiro válido.")
            queryset = queryset.filter(
                installments__due_date__gte=datetime.date(year_int, 1, 1),
                installments__due_date__lt=datetime.date(year_int + 1, 1, 1),
            ).distinct()

        return queryset.prefetch_related("installments")

    def list(self, request, *args, **kwargs):
        firm_id = self._get_firm_id()
        year = request.query_params.get("year", "all")
        month = request.query_params.get("month", "all")
        start_date = request.query_params.get("start_date", "")
        end_date = request.query_params.get("end_date", "")
        cache_key = f"honorarios:{firm_id}:{year}:{month}:{start_date}:{end_date}"

        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        cache.set(cache_key, serializer.data, timeout=300)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        track_event(
            user=request.user,
            event_name="honorario_criado_sucesso",
            properties={
                "honorario_id": serializer.data.get("id"),
                "amount": float(serializer.data.get("amount", 0)),
                "status_inicial": serializer.data.get("status"),
                "has_installments": len(serializer.data.get("installments", [])) > 0
            }
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Autenticação necessária.")

        firm_id = self._get_firm_id()
        if not firm_id:
            raise ValidationError("O usuário não está vinculado a nenhuma empresa (firm).")
        serializer.save(firm_id=firm_id)
        invalidar_cache_financeiro(firm_id)

    @action(detail=True, methods=["patch"], url_path=r"installments/(?P<installment_pk>[^/.]+)")
    def update_installment(self, request, pk=None, installment_pk=None):
        honorario = self.get_object()
        parcela = get_object_or_404(ParcelaHonorario, honorario=honorario, id=installment_pk)

        serializer = ParcelaHonorarioSerializer(parcela, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_installment = serializer.save()
        invalidar_cache_financeiro(self._get_firm_id())

        track_event(
            user=request.user,
            event_name="honorarios_parcela_recebida",
            properties={
                "honorario_id": str(honorario.id),
                "installment_id": str(updated_installment.id),
                "installment_number": updated_installment.installment_number,
                "amount": float(updated_installment.amount)
            }
        )

        return Response(serializer.data, status=status.HTTP_200_OK)