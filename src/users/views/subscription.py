from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import transaction

from ...finance.services.stripe_service import StripeService
from ...firms.models.subscription import Plan, FirmSubscription
from ...users.utils.telemetry import track_event


class CriarAssinaturaView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_active_plan(self, plan_identifier):
        if not plan_identifier:
            return None

        plan_identifier = str(plan_identifier).strip()

        if plan_identifier.isdigit():
            return Plan.objects.filter(id=int(plan_identifier), is_active=True).first()

        return Plan.objects.filter(stripe_price_id=plan_identifier, is_active=True).first()

    def _bootstrap_plan_from_stripe_price(self, stripe_price_id):
        plan, _ = Plan.objects.get_or_create(
            stripe_price_id=stripe_price_id,
            defaults={
                "name": f"Stripe {stripe_price_id[:40]}",
                "price": "0.00",
                "cycle": Plan.CycleType.MONTHLY,
                "is_active": True,
            },
        )
        return plan

    def post(self, request):
        plan_id = request.data.get("plan_id")
        if not plan_id:
            track_event(
                user=request.user,
                event_name="assinatura_checkout_falha",
                properties={"motivo_erro": "plan_id nao fornecido"},
            )
            raise ValidationError({"plan_id": "Este campo é obrigatório para iniciar a assinatura."})

        plan_identifier = str(plan_id).strip()
        plan = self._get_active_plan(plan_identifier)

        if not plan and plan_identifier.startswith("price_"):
            plan = self._bootstrap_plan_from_stripe_price(plan_identifier)

        if not plan:
            track_event(
                user=request.user,
                event_name="assinatura_checkout_falha",
                properties={"plan_id_tentado": plan_id, "motivo_erro": "plano_invalido_ou_inativo"},
            )
            raise ValidationError({"plan_id": "O plano selecionado não está disponível ou é inválido."})

        membership = request.user.firm_memberships.first()
        if not membership:
            track_event(
                user=request.user,
                event_name="assinatura_checkout_falha",
                properties={"motivo_erro": "usuario_sem_escritorio_associado"},
            )
            raise ValidationError({"detail": "Operação negada. O usuário corrente não possui um escritório associado."})
        firm = membership.firm

        try:
            with transaction.atomic():
                subscription, created = FirmSubscription.objects.get_or_create(
                    firm=firm,
                    defaults={"plan": plan, "status": FirmSubscription.SubscriptionStatus.PENDING},
                )

                if not created and subscription.status == FirmSubscription.SubscriptionStatus.PENDING:
                    subscription.plan = plan
                    subscription.save()

                service = StripeService()
                dados_checkout = service.criar_checkout_session(
                    stripe_price_id=plan.stripe_price_id,
                    firm_subscription_id=subscription.id,
                    firm_id=str(firm.id),
                    plan_name=plan.name,
                    user_email=request.user.email,
                )

            track_event(
                user=request.user,
                event_name="assinatura_checkout_iniciado",
                properties={
                    "plan_id": plan.id,
                    "plan_name": plan.name,
                    "subscription_id": subscription.id,
                    "stripe_price_id": plan.stripe_price_id,
                },
            )

            return Response({
                "checkout_url": dados_checkout["checkout_url"],
                "subscription_id": subscription.id,
                "status": subscription.status,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            track_event(
                user=request.user,
                event_name="assinatura_checkout_falha",
                properties={"plan_id": plan.id, "plan_name": plan.name, "motivo_erro": f"erro_gateway: {str(e)}"},
            )
            raise e


class ListarPlanosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = StripeService()
        planos = service.listar_planos()
        return Response({
            "data": planos,
            "stripe_publishable_key": service.publishable_key,
        }, status=status.HTTP_200_OK)
