from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models.honorarios import Honorario
from ..serializers.honorarios import HonorarioSerializer
from ...users.utils.telemetry import track_event


class HonorarioViewSet(viewsets.ModelViewSet):
    serializer_class = HonorarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_firm(self, user):
        membership = user.firm_memberships.first()
        if not membership:
            raise ValidationError("O usuário não está vinculado a nenhuma empresa (firm).")
        return membership.firm

    def get_queryset(self):
        queryset = Honorario.objects.filter(
            firm__members__user=self.request.user
        ).prefetch_related('installments')

        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")

        if year:
            try:
                queryset = queryset.filter(date__year=int(year))
            except ValueError:
                track_event(
                    user=self.request.user,
                    event_name="honorarios_filtro_erro",
                    properties={"year_tentado": year, "motivo": "ano_invalido"}
                )
                raise ValidationError("O parâmetro 'year' deve ser um número inteiro válido.")

        if month:
            try:
                queryset = queryset.filter(date__month=int(month))
            except ValueError:
                track_event(
                    user=self.request.user,
                    event_name="honorarios_filtro_erro",
                    properties={"month_tentado": month, "motivo": "mes_invalido"}
                )
                raise ValidationError("O parâmetro 'month' deve ser um número inteiro válido.")

        return queryset

    def list(self, request, *args, **kwargs):
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        if year or month:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return super().list(request, *args, **kwargs)

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

        firm = self._get_user_firm(user)
        serializer.save(firm=firm)