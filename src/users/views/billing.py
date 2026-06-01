from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action

from ..models.billing import Subscription
from ..serializers.billing import SubscriptionSerializer
from ...users.utils.telemetry import track_event


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

        track_event(
            user=request.user,
            event_name="billing_view_assinatura",
            properties={
                "subscription_id": instance.id,
                "plan_name": instance.plan.name if hasattr(instance, 'plan') and instance.plan else "N/A",
                "status_assinatura": instance.status if hasattr(instance, 'status') else "N/A"
            }
        )

        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="prepare-upgrade")
    def prepare_upgrade(self, request):
        """
        Espaço reservado para quando você integrar o Gateway.
        Aqui você receberá o novo 'plan_id' do front-end, chamará a classe de 
        serviço do gateway, atualizará no Stripe/Asaas e mudará o plano aqui.
        """
        new_plan_id = request.data.get("plan_id")

        track_event(
            user=request.user,
            event_name="billing_intencao_upgrade",
            properties={
                "plan_id_pretendido": new_plan_id
            }
        )

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
        track_event(
            user=request.user,
            event_name="billing_intencao_cancelamento"
        )

        return Response(
            {"detail": "Rota preparada. Integração com gateway pendente."},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )