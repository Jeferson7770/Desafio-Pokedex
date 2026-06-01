from ..models.firm_member import FirmMember
from ..models.firm_structure import Firm
from ..serializers.firm import FirmSerializer, FirmCreateSerializer, FirmMemberSerializer
from ...users.utils.telemetry import track_event

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

class FirmViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Firm.objects.filter(members__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return FirmCreateSerializer
        return FirmSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        firm = serializer.save()
        
        track_event(
            user=request.user,
            event_name="escritorio_criado_sucesso",
            properties={
                "firm_id": str(firm.id),
                "firm_name": firm.name
            }
        )
        
        response_serializer = FirmSerializer(firm)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        members = FirmMember.objects.filter(
            firm_id=pk,
            firm__members__user=request.user
        )
        serializer = FirmMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_member(self, request, pk=None):
        serializer = FirmMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        member = serializer.save(firm_id=pk)
        
        track_event(
            user=request.user,
            event_name="escritorio_membro_adicionado",
            properties={
                "firm_id": str(pk),
                "novo_membro_role": member.role if hasattr(member, 'role') else "N/A"
            }
        )
        
        response_serializer = FirmMemberSerializer(member)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)