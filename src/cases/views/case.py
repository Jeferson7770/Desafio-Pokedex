from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from ..models.case_structure import Client, Process
from ..serializers.case import CaseSerializer, ClientSerializer, ProcessSerializer


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
        serializer.save(firm=self._get_user_firm())


class ProcessViewSet(BaseFirmScopedViewSet):
    serializer_class = ProcessSerializer

    def get_queryset(self):
        return Process.objects.filter(
            firm__members__user=self.request.user,
        ).select_related("client")

    def perform_create(self, serializer):
        serializer.save(firm=self._get_user_firm())


class CaseViewSet(ProcessViewSet):
    serializer_class = CaseSerializer