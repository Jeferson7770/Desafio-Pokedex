from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_not_found

from ..models.laywer import LawyerProfile
from ..serializers.laywer import LawyerProfileSerializer


class LawyerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = LawyerProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        """
        Garante que o usuário só consiga listar/enxergar o seu próprio perfil.
        """
        return LawyerProfile.objects.filter(user=self.request.user)

    def get_object(self):
        """
        Sobrescreve a busca do objeto para ignorar a necessidade de passar um ID 
        na URL (ex: /api/profile/ em vez de /api/profile/1/).
        """
        queryset = self.get_queryset()
        obj = queryset.first()
        if not obj:
            from django.http import Http404
            raise Http404("Nenhum perfil encontrado para o usuário autenticado.")
        
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        """
        Modifica o comportamento de listagem (GET /) para retornar direto 
        o objeto do perfil, em vez de uma lista/array contendo um único item.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)