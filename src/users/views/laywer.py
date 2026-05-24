from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from ..models.laywer import LawyerProfile
from ..serializers.laywer import LawyerProfileSerializer


class LawyerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = LawyerProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return LawyerProfile.objects.filter(user=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.first()
        if not obj:
            from django.http import Http404
            raise Http404("Nenhum perfil encontrado para o usuário autenticado.")
        
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        """
        Rota interna para o advogado alterar sua própria senha estando logado.
        POST /api/auth/laywer-profile/change-password/
        """
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not current_password or not new_password:
            raise ValidationError(
                {"detail": "Os campos 'current_password' e 'new_password' são obrigatórios."}
            )

        if not user.check_password(current_password):
            return Response(
                {"current_password": ["A senha atual está incorreta."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        
        return Response(
            {"message": "Senha alterada com sucesso!"},
            status=status.HTTP_200_OK
        )