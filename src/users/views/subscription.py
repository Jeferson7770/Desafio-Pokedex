from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import transaction

from ...dinheiro.services.abacatepay import AbacatePayService
from ...firms.models.subscription import Plan, FirmSubscription

class CriarAssinaturaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        if not plan_id:
            raise ValidationError({"plan_id": "Este campo é obrigatório para iniciar a assinatura."})

        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            raise ValidationError({"plan_id": "O plano selecionado não está disponível ou é inválido."})

        membership = request.user.firm_memberships.first()
        if not membership:
            raise ValidationError({"detail": "Operação negada. O usuário corrente não possui um escritório associado."})
        firm = membership.firm

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
                external_id=subscription.id,  # Referência da assinatura interna do seu sistema
                metadata=metadata_customizado
            )

            billing_id = dados_checkout.get("data", {}).get("id")
            checkout_url = dados_checkout.get("data", {}).get("url")

            subscription.abacatepay_billing_id = billing_id
            subscription.save()

        return Response({
            "checkout_url": checkout_url,
            "subscription_id": subscription.id,
            "status": subscription.status
        }, status=status.HTTP_200_OK)