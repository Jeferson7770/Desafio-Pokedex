from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone

import stripe as stripe_sdk
from decouple import config

from ...finance.services.stripe_service import StripeService
from ...firms.models.subscription import Plan, FirmSubscription
from ...users.utils.telemetry import track_event, track_system_event


class CriarAssinaturaView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_active_plan(self, plan_identifier):
        if not plan_identifier:
            return None

        plan_identifier = str(plan_identifier).strip()

        if plan_identifier.isdigit():
            return Plan.objects.filter(id=int(plan_identifier), is_active=True).first()

        return Plan.objects.filter(stripe_price_id=plan_identifier, is_active=True).first()

    @staticmethod
    def _stripe_cycle(recurring):
        if not recurring:
            return Plan.CycleType.MONTHLY
        interval = getattr(recurring, "interval", None)
        count = getattr(recurring, "interval_count", 1) or 1
        if interval == "year":
            return Plan.CycleType.ANNUALLY
        if interval == "week":
            return Plan.CycleType.WEEKLY
        # interval == "month"
        if count >= 12:
            return Plan.CycleType.ANNUALLY
        if count >= 6:
            return Plan.CycleType.SEMIANNUALLY
        if count >= 3:
            return Plan.CycleType.QUARTERLY
        return Plan.CycleType.MONTHLY

    def _bootstrap_plan_from_stripe_price(self, stripe_price_id):
        defaults = {
            "name": f"Stripe {stripe_price_id[:40]}",
            "price": "0.00",
            "cycle": Plan.CycleType.MONTHLY,
            "is_active": True,
        }
        try:
            import stripe as stripe_sdk
            from decouple import config
            stripe_sdk.api_key = config("STRIPE_SECRET_KEY")
            price = stripe_sdk.Price.retrieve(stripe_price_id, expand=["product"])
            defaults["name"] = getattr(price.product, "name", defaults["name"])
            defaults["price"] = str(int(getattr(price, "unit_amount", 0) or 0) / 100)
            defaults["cycle"] = self._stripe_cycle(getattr(price, "recurring", None))
            defaults["is_active"] = getattr(price, "active", True)
        except Exception:
            pass

        plan, created = Plan.objects.get_or_create(stripe_price_id=stripe_price_id, defaults=defaults)
        if not created:
            for field, value in defaults.items():
                setattr(plan, field, value)
            plan.save(update_fields=list(defaults.keys()))

        if created:
            track_system_event("plano_criado_automaticamente", {
                "stripe_price_id": stripe_price_id,
                "plan_id": plan.id,
                "plan_name": plan.name,
                "cycle": plan.cycle,
                "price": str(plan.price),
            })

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

                upgradeable = (
                    FirmSubscription.SubscriptionStatus.PENDING,
                    FirmSubscription.SubscriptionStatus.TRIAL,
                )
                if not created and subscription.status in upgradeable:
                    subscription.plan = plan
                    subscription.save(update_fields=["plan", "updated_at"])

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


class CancelarAssinaturaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reason = request.data.get("reason", "")
        feedback = request.data.get("feedback", "")

        membership = request.user.firm_memberships.first()
        if not membership:
            raise ValidationError({"detail": "Usuário sem escritório associado."})

        try:
            sub = membership.firm.subscription
        except FirmSubscription.DoesNotExist:
            raise ValidationError({"detail": "Nenhuma assinatura encontrada para este escritório."})

        if sub.status != FirmSubscription.SubscriptionStatus.ACTIVE:
            track_event(
                user=request.user,
                event_name="assinatura_cancelamento_falha",
                properties={"motivo_erro": "status_nao_ativo", "status_atual": sub.status},
            )
            raise PermissionDenied("Apenas assinaturas ativas podem ser canceladas.")

        if not sub.stripe_subscription_id:
            track_event(
                user=request.user,
                event_name="assinatura_cancelamento_falha",
                properties={"motivo_erro": "stripe_subscription_id_ausente"},
            )
            raise ValidationError({"detail": "Assinatura sem ID Stripe — entre em contato com o suporte."})

        stripe_sdk.api_key = config("STRIPE_SECRET_KEY")
        stripe_sdk.Subscription.modify(
            sub.stripe_subscription_id,
            cancel_at_period_end=True,
        )

        sub.cancel_reason = reason or None
        sub.cancel_feedback = feedback or None
        sub.cancelled_at = timezone.now()
        sub.save(update_fields=["cancel_reason", "cancel_feedback", "cancelled_at", "updated_at"])

        track_event(
            user=request.user,
            event_name="assinatura_cancelamento_solicitado",
            properties={
                "stripe_subscription_id": sub.stripe_subscription_id,
                "cancel_reason": reason,
                "tem_feedback": bool(feedback),
                "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            },
        )

        return Response(
            {"detail": "Assinatura cancelada ao fim do período."},
            status=status.HTTP_200_OK,
        )


class ListarPlanosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = StripeService()
        try:
            planos = service.listar_planos()
        except Exception as e:
            track_event(
                user=request.user,
                event_name="planos_listagem_falha",
                properties={"erro": str(e)},
            )
            raise

        track_event(
            user=request.user,
            event_name="planos_listados",
            properties={"total_planos": len(planos)},
        )
        return Response({
            "data": planos,
            "stripe_publishable_key": service.publishable_key,
        }, status=status.HTTP_200_OK)
