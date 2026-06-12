from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from ..models.case_structure import Client, Process
from ..serializers.case import CaseSerializer, ClientSerializer, ProcessSerializer
from ...users.utils.telemetry import track_event
from ...users.utils.firm_mixin import FirmMixin


class BaseFirmScopedViewSet(FirmMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]


class ClientViewSet(BaseFirmScopedViewSet):
    serializer_class = ClientSerializer

    def get_queryset(self):
        firm_id = self._get_firm_id()
        if not firm_id:
            return Client.objects.none()
        return Client.objects.filter(firm_id=firm_id).order_by("name")

    def perform_create(self, serializer):
        firm_id = self._get_firm_id()
        if not firm_id:
            raise ValidationError("O usuario nao possui nenhuma empresa vinculada.")
        client = serializer.save(firm_id=firm_id)
        track_event(
            user=self.request.user,
            event_name="cliente_criado_sucesso",
            properties={"client_id": client.id, "client_type": client.type},
        )

    def perform_destroy(self, instance):
        track_event(
            user=self.request.user,
            event_name="cliente_deletado",
            properties={"client_id": instance.id, "client_name": instance.name},
        )
        instance.delete()


class ProcessViewSet(BaseFirmScopedViewSet):
    serializer_class = ProcessSerializer

    def get_queryset(self):
        firm_id = self._get_firm_id()
        if not firm_id:
            return Process.objects.none()
        return Process.objects.filter(firm_id=firm_id).select_related("client")

    def perform_create(self, serializer):
        firm_id = self._get_firm_id()
        if not firm_id:
            raise ValidationError("O usuario nao possui nenhuma empresa vinculada.")
        process = serializer.save(firm_id=firm_id)
        track_event(
            user=self.request.user,
            event_name="processo_criado_sucesso",
            properties={
                "process_id": process.id,
                "payment_type": process.payment_type,
                "client_id": process.client_id,
            },
        )

    def perform_destroy(self, instance):
        track_event(
            user=self.request.user,
            event_name="processo_deletado",
            properties={"process_id": instance.id, "process_title": instance.title},
        )
        instance.delete()


class CaseViewSet(ProcessViewSet):
    serializer_class = CaseSerializer
