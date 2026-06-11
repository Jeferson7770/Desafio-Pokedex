from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models.outras_entradas import OutraEntrada, OutraEntradaInstallment
from ..serializers.outras_entradas import OutraEntradaSerializer, OutraEntradaInstallmentSerializer
from ...users.utils.telemetry import track_event


class OutraEntradaViewSet(viewsets.ModelViewSet):
    serializer_class = OutraEntradaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_firm(self, user):
        membership = user.firm_memberships.first()
        if not membership:
            raise ValidationError("O usuário não está vinculado a nenhuma empresa (firm).")
        return membership.firm

    def get_queryset(self):
        firm = self._get_user_firm(self.request.user)
        queryset = OutraEntrada.objects.filter(firm=firm).prefetch_related("installments")

        if self.action != "list":
            return queryset

        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        month_filter = bool(year or month)
        range_filter = bool(start_date or end_date)

        if not month_filter and not range_filter:
            raise ValidationError("Informe year+month ou start_date+end_date para filtrar a listagem.")

        if month_filter and range_filter:
            raise ValidationError("Use apenas um tipo de filtro por vez: year+month ou start_date+end_date.")

        if month_filter:
            if not year or not month:
                raise ValidationError("Para filtro mensal, informe os parâmetros year e month juntos.")
            try:
                year_int = int(year)
                month_int = int(month)
            except ValueError:
                raise ValidationError("Os parâmetros 'year' e 'month' devem ser números inteiros válidos.")

            if month_int < 1 or month_int > 12:
                raise ValidationError("O parâmetro 'month' deve estar entre 1 e 12.")

            return queryset.filter(date__year=year_int, date__month=month_int)

        if not start_date or not end_date:
            raise ValidationError("Para filtro por período, informe os parâmetros start_date e end_date juntos.")

        return queryset.filter(date__range=[start_date, end_date])

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Autenticação necessária.")

        firm = self._get_user_firm(self.request.user)
        instance = serializer.save(firm=firm)
        track_event(
            user=self.request.user,
            event_name="outra_entrada_criada_sucesso",
            properties={
                "outra_entrada_id": instance.id,
                "amount": float(instance.amount),
                "is_installment": instance.is_installment,
            },
        )

    def perform_destroy(self, instance):
        track_event(
            user=self.request.user,
            event_name="outra_entrada_deletada",
            properties={"outra_entrada_id": instance.id, "title": instance.title},
        )
        instance.delete()

    @action(detail=True, methods=["patch"], url_path=r"installments/(?P<installment_pk>[^/.]+)")
    def update_installment(self, request, pk=None, installment_pk=None):
        outra_entrada = self.get_object()
        installment = get_object_or_404(
            OutraEntradaInstallment,
            outra_entrada=outra_entrada,
            id=installment_pk,
        )

        serializer = OutraEntradaInstallmentSerializer(installment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        statuses = outra_entrada.installments.values_list("status", flat=True)
        if statuses and all(s == OutraEntradaInstallment.Status.RECEBIDO for s in statuses):
            outra_entrada.status = OutraEntrada.Status.RECEBIDO
        else:
            outra_entrada.status = OutraEntrada.Status.PENDENTE
        outra_entrada.save(update_fields=["status"])

        track_event(
            user=self.request.user,
            event_name="outra_entrada_parcela_atualizada",
            properties={
                "outra_entrada_id": outra_entrada.id,
                "installment_id": installment.id,
                "novo_status": installment.status,
                "outra_entrada_status": outra_entrada.status,
            },
        )

        return Response(serializer.data, status=status.HTTP_200_OK)
