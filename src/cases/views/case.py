from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from ..models.case_structure import Client, Process
from ..serializers.case import CaseSerializer, ClientSerializer, ProcessSerializer
from ...users.utils.telemetry import track_event


class BaseFirmScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_firm(self):
        membership = self.request.user.firm_memberships.first()
        if not membership:
            raise ValidationError("O usuario nao possui nenhuma empresa vinculada.")
        return membership.firm


class ClientViewSet(BaseFirmScopedViewSet):
    serializer_class = ClientSerializer

    def get_queryset(self):
        return Client.objects.filter(
            firm__members__user=self.request.user,
        ).order_by("name")

    def perform_create(self, serializer):
        client = serializer.save(firm=self._get_user_firm())
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
        return Process.objects.filter(
            firm__members__user=self.request.user,
        ).select_related("client")

    def perform_create(self, serializer):
        process = serializer.save(firm=self._get_user_firm())
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