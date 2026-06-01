from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models.suggestions_structure import Suggestion
from ..serializers.suggestions import SuggestionSerializer
from ...users.utils.telemetry import track_event


class SuggestionViewSet(viewsets.ModelViewSet):
    serializer_class = SuggestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_firm(self, user):
        """
        Método auxiliar para buscar a empresa vinculada ao usuário.
        Segue o mesmo padrão de segurança da ExpenseViewSet.
        """
        membership = user.firm_memberships.first()
        if not membership:
            raise ValidationError("O seu usuário não está vinculado a nenhuma empresa (firm).")
        return membership.firm

    def get_queryset(self):
        firm = self._get_user_firm(self.request.user)
        return Suggestion.objects.filter(firm=firm).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        track_event(
            user=request.user,
            event_name="sugestao_enviada_sucesso",
            properties={
                "suggestion_id": serializer.data.get("id"),
                "categoria": serializer.data.get("category", "N/A")
            }
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Você precisa estar autenticado para enviar uma sugestão.")
            
        firm = self._get_user_firm(self.request.user)
        serializer.save(firm=firm)