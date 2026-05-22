from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models.suggestions_structure import Suggestion
from ..serializers.suggestions import SuggestionSerializer

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

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Você precisa estar autenticado para enviar uma sugestão.")
            
        firm = self._get_user_firm(self.request.user)
        serializer.save(firm=firm)