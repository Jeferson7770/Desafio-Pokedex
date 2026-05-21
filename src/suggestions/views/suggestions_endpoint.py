from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from ..models.suggestions_structure import Suggestion
from ..serializers.suggestions import SuggestionSerializer

class SuggestionViewSet(viewsets.ModelViewSet):
    serializer_class = SuggestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Suggestion.objects.filter(firm=self.request.user.firm).order_by("-created_at")

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Você precisa estar autenticado para enviar uma sugestão.")
            
        serializer.save(firm=self.request.user.firm)