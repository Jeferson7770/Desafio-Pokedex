from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action

from ..models.billing import Subscription
from ..serializers.billing import SubscriptionSerializer

class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.first()
        if not obj:
            from django.http import Http404
            raise Http404("Nenhuma assinatura ativa vinculada a este usuário.")
        return obj

    def list(self, request, *args, **kwargs):
        """ Retorna direto o objeto da assinatura (Igual fizemos no Perfil) """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="prepare-upgrade")
    def prepare_upgrade(self, request):
        """
        Espaço reservado para quando você integrar o Gateway.
        Aqui você receberá o novo 'plan_id' do front-end, chamará a classe de 
        serviço do gateway, atualizará no Stripe/Asaas e mudará o plano aqui.
        """
        return Response(
            {"detail": "Rota preparada. Integração com gateway pendente."},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

    @action(detail=False, methods=["post"], url_path="prepare-cancel")
    def prepare_cancel(self, request):
        """
        Espaço reservado para o botão 'Cancelar Assinatura'.
        No futuro, disparará uma chamada de cancelamento para o gateway.
        """
        return Response(
            {"detail": "Rota preparada. Integração com gateway pendente."},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )