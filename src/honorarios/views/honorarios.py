from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from ..models.honorarios import Honorario
from ..serializers.honorarios import HonorarioSerializer


class HonorarioViewSet(viewsets.ModelViewSet):
    serializer_class = HonorarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_firm(self, user):
        """
        Garante o isolamento por empresa buscando a membership ativa do usuário.
        """
        membership = user.firm_memberships.first()
        if not membership:
            raise ValidationError("O usuário não está vinculado a nenhuma empresa (firm).")
        return membership.firm

    def get_queryset(self):
        queryset = Honorario.objects.filter(
            firm__members__user=self.request.user
        )

        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")

        if year:
            try:
                queryset = queryset.filter(date__year=int(year))
            except ValueError:
                raise ValidationError("O parâmetro 'year' deve ser um número inteiro válido.")

        if month:
            try:
                queryset = queryset.filter(date__month=int(month))
            except ValueError:
                raise ValidationError("O parâmetro 'month' deve ser um número inteiro válido.")

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Sobrescreve a listagem para forçar que consultas filtradas por data 
        retornem um array limpo [ ... ] sem quebras de paginação global.
        """
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        if year or month:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Autenticação necessária.")

        firm = self._get_user_firm(user)
        serializer.save(firm=firm)