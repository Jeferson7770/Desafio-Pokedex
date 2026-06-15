import logging
from datetime import datetime, timezone

import stripe
from decouple import config
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from ..models.subscription import FirmSubscription
from ...users.utils.telemetry import track_event, track_system_event

logger = logging.getLogger(__name__)


def _attr(obj, key, default=None):
    """Acesso seguro a atributos de objetos Stripe SDK v15 (não suportam .get())."""
    try:
        return getattr(obj, key, default)
    except Exception:
        return default


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        sig_header = request.headers.get("Stripe-Signature", "")
        webhook_secret = config("STRIPE_WEBHOOK_SECRET", default="")

        try:
            event = stripe.Webhook.construct_event(
                payload=request.body,
                sig_header=sig_header,
                secret=webhook_secret,
            )
        except stripe.error.SignatureVerificationError:
            logger.warning("Stripe webhook: assinatura inválida rejeitada")
            track_system_event("stripe_webhook_assinatura_invalida")
            return Response({"detail": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Stripe webhook: erro ao construir evento — %s", str(e))
            track_system_event("stripe_webhook_erro_construcao", {"erro": str(e)})
            return Response({"detail": "Webhook error."}, status=status.HTTP_400_BAD_REQUEST)

        event_type = event["type"]
        event_id = event["id"]
        data = event["data"]["object"]

        logger.info("Stripe webhook recebido: type=%s id=%s", event_type, event_id)
        track_system_event("stripe_webhook_recebido", {"event_type": event_type, "event_id": event_id})

        try:
            if event_type == "checkout.session.completed":
                self._handle_checkout_completed(data)
            elif event_type == "invoice.paid":
                self._handle_invoice_paid(data)
            elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
                self._handle_subscription_changed(data, event_type)
        except Exception as e:
            logger.error("Stripe webhook: erro ao processar event=%s — %s", event_type, str(e), exc_info=True)
            track_system_event("stripe_webhook_erro_processamento", {"event_type": event_type, "event_id": event_id, "erro": str(e)})
            return Response({"detail": "Processing error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "ok"}, status=status.HTTP_200_OK)

    def _handle_checkout_completed(self, session):
        metadata = _attr(session, "metadata") or {}
        firm_subscription_id = metadata.get("firm_subscription_id") if hasattr(metadata, "get") else _attr(metadata, "firm_subscription_id")

        if not firm_subscription_id:
            logger.warning("Stripe webhook checkout.session.completed: metadata.firm_subscription_id ausente")
            track_system_event("stripe_webhook_metadata_ausente", {"event_type": "checkout.session.completed"})
            return

        subscription = FirmSubscription.objects.filter(id=firm_subscription_id).first()
        if not subscription:
            logger.warning("Stripe webhook: FirmSubscription %s não encontrada", firm_subscription_id)
            track_system_event("stripe_webhook_subscription_nao_encontrada", {"event_type": "checkout.session.completed", "firm_subscription_id": firm_subscription_id})
            return

        subscription.status = FirmSubscription.SubscriptionStatus.ACTIVE
        subscription.stripe_subscription_id = _attr(session, "subscription")
        subscription.stripe_customer_id = _attr(session, "customer")
        subscription.save(update_fields=["status", "stripe_subscription_id", "stripe_customer_id", "updated_at"])

        logger.info("Stripe webhook: FirmSubscription %s → ACTIVE (checkout.session.completed)", subscription.id)
        self._track(subscription, "checkout.session.completed")

    def _handle_invoice_paid(self, invoice):
        stripe_sub_id = _attr(invoice, "subscription")
        if not stripe_sub_id:
            track_system_event("stripe_webhook_metadata_ausente", {"event_type": "invoice.paid", "campo": "subscription"})
            return

        subscription = FirmSubscription.objects.filter(stripe_subscription_id=stripe_sub_id).first()
        if not subscription:
            track_system_event("stripe_webhook_subscription_nao_encontrada", {"event_type": "invoice.paid", "stripe_subscription_id": stripe_sub_id})
            return

        subscription.status = FirmSubscription.SubscriptionStatus.ACTIVE

        try:
            lines = _attr(invoice, "lines")
            lines_data = _attr(lines, "data") or []
            if lines_data:
                period = _attr(lines_data[0], "period")
                period_end = _attr(period, "end") if period else None
                if period_end:
                    subscription.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
        except Exception:
            pass

        subscription.save(update_fields=["status", "current_period_end", "updated_at"])
        logger.info("Stripe webhook: FirmSubscription %s → ACTIVE (invoice.paid)", subscription.id)
        self._track(subscription, "invoice.paid")

    def _handle_subscription_changed(self, stripe_sub, event_type):
        stripe_sub_id = _attr(stripe_sub, "id")
        subscription = FirmSubscription.objects.filter(stripe_subscription_id=stripe_sub_id).first()
        if not subscription:
            track_system_event("stripe_webhook_subscription_nao_encontrada", {"event_type": event_type, "stripe_subscription_id": stripe_sub_id})
            return

        stripe_status = _attr(stripe_sub, "status")
        update_fields = ["updated_at"]

        if event_type == "customer.subscription.deleted" or stripe_status == "canceled":
            subscription.status = FirmSubscription.SubscriptionStatus.CANCELLED
            update_fields.append("status")
        elif stripe_status == "active":
            subscription.status = FirmSubscription.SubscriptionStatus.ACTIVE
            update_fields.append("status")

        period_end = _attr(stripe_sub, "current_period_end")
        if period_end:
            subscription.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
            update_fields.append("current_period_end")

        subscription.save(update_fields=update_fields)
        logger.info("Stripe webhook: FirmSubscription %s atualizada (event=%s)", subscription.id, event_type)
        self._track(subscription, event_type)

    def _track(self, subscription, event_type):
        try:
            membership = subscription.firm.members.select_related("user").first()
            if membership:
                track_event(
                    user=membership.user,
                    event_name="webhook_assinatura_atualizada",
                    properties={
                        "evento_stripe": event_type,
                        "subscription_id": subscription.id,
                        "novo_status": subscription.status,
                        "firm_id": subscription.firm.id,
                    },
                )
        except Exception:
            pass
