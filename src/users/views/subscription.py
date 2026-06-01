from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import transaction

from ...dinheiro.services.abacatepay import AbacatePayService
from ...firms.models.subscription import Plan, FirmSubscription
from ...users.utils.telemetry import track_event


class CriarAssinaturaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        if not plan_id:
            track_event(
                user=request.user,
                event_name="assinatura_checkout_falha",
                properties={"motivo_erro": "plan_id nao fornecido"}
            )
            raise ValidationError({"plan_id": "Este campo é obrigatório para iniciar a assinatura."})

        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            track_event(
                user=request.user,
                event_name="assinatura_checkout_falha",
                properties={
                    "plan_id_tentado": plan_id,
                    "motivo_erro": "plano_invalido_ou_inativo"
                }
            )
            raise ValidationError({"plan_id": "O plano selecionado não está disponível ou é inválido."})

        membership = request.user.firm_memberships.first()
        if not membership:
            track_event(
                user=request.user,
                event_name="assinatura_checkout_falha",
                properties={"motivo_erro": "usuario_sem_escritorio_associado"}
            )
            raise ValidationError({"detail": "Operação negada. O usuário corrente não possui um escritório associado."})
        firm = membership.firm

        try:
            with transaction.atomic():
                subscription, created = FirmSubscription.objects.get_or_create(
                    firm=firm,
                    defaults={"plan": plan, "status": FirmSubscription.SubscriptionStatus.PENDING}
                )

                if not created and subscription.status == FirmSubscription.SubscriptionStatus.PENDING:
                    subscription.plan = plan
                    subscription.save()

                service = AbacatePayService()
                metadata_customizado = {
                    "firm_id": str(firm.id),
                    "plan_name": plan.name,
                    "user_email": request.user.email
                }
                
                dados_checkout = service.criar_checkout_assinatura(
                    produto_id=plan.abacatepay_product_id,
                    external_id=subscription.id,
                    metadata=metadata_customizado
                )

                billing_id = dados_checkout.get("data", {}).get("id")
                checkout_url = dados_checkout.get("data", {}).get("url")

                subscription.abacatepay_billing_id = billing_id
                subscription.save()

            track_event(
                user=request.user,
                event_name="assinatura_checkout_iniciado",
                properties={
                    "plan_id": plan.id,
                    "plan_name": plan.name,
                    "subscription_id": subscription.id,
                    "abacatepay_billing_id": billing_id
                }
            )

            return Response({
                "checkout_url": checkout_url,
                "subscription_id": subscription.id,
                "status": subscription.status
            }, status=status.HTTP_200_OK)

        except Exception as e:
            track_event(
                user=request.user,
                event_name="assinatura_checkout_falha",
                properties={
                    "plan_id": plan.id,
                    "plan_name": plan.name,
                    "motivo_erro": f"erro_gateway: {str(e)}"
                }
            )
            raise e