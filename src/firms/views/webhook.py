import hmac
import hashlib
import base64
import logging
from datetime import datetime

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from ..models.subscription import FirmSubscription
from ...users.utils.telemetry import track_event

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AbacatePayWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def _verify_signature(self, request):
        secret = getattr(settings, 'ABACATEPAY_WEBHOOK_SECRET', '')
        if not secret:
            logger.warning("ABACATEPAY_WEBHOOK_SECRET não configurado — validação de assinatura ignorada")
            return True

        received = request.headers.get("X-Webhook-Signature", "")
        if not received:
            return False

        expected = base64.b64encode(
            hmac.new(secret.encode('utf-8'), request.body, hashlib.sha256).digest()
        ).decode('utf-8')

        return hmac.compare_digest(expected, received)

    def post(self, request):
        if not self._verify_signature(request):
            logger.warning("AbacatePay webhook: assinatura inválida rejeitada")
            return Response({"detail": "Invalid signature."}, status=status.HTTP_403_FORBIDDEN)

        event = request.data.get("event")
        data = request.data.get("data", {})

        billing_id = data.get("id")
        external_id = data.get("externalId")

        logger.info("AbacatePay webhook recebido: event=%s billing_id=%s", event, billing_id)

        if not billing_id and not external_id:
            return Response({"detail": "Missing event data."}, status=status.HTTP_400_BAD_REQUEST)

        subscription = self._find_subscription(billing_id, external_id)
        if not subscription:
            logger.warning(
                "AbacatePay webhook: assinatura não encontrada (billing_id=%s, external_id=%s)",
                billing_id, external_id,
            )
            return Response({"detail": "ok"}, status=status.HTTP_200_OK)

        if event in ("subscription.completed", "subscription.renewed"):
            self._handle_activated(subscription, data, event)

        elif event == "subscription.cancelled":
            self._handle_cancelled(subscription, event)

        return Response({"detail": "ok"}, status=status.HTTP_200_OK)

    def _find_subscription(self, billing_id, external_id):
        if billing_id:
            sub = FirmSubscription.objects.filter(abacatepay_billing_id=billing_id).first()
            if sub:
                return sub
        if external_id and str(external_id).isdigit():
            return FirmSubscription.objects.filter(id=int(external_id)).first()
        return None

    def _handle_activated(self, subscription, data, event):
        subscription.status = FirmSubscription.SubscriptionStatus.ACTIVE

        period_end_raw = data.get("currentPeriodEnd") or data.get("nextBillingDate")
        if period_end_raw:
            try:
                subscription.current_period_end = datetime.fromisoformat(
                    period_end_raw.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        subscription.save()
        logger.info("AbacatePay webhook: subscription %s → ACTIVE (event=%s)", subscription.id, event)
        self._track(subscription, event)

    def _handle_cancelled(self, subscription, event):
        subscription.status = FirmSubscription.SubscriptionStatus.CANCELLED
        subscription.save()
        logger.info("AbacatePay webhook: subscription %s → CANCELLED", subscription.id)
        self._track(subscription, event)

    def _track(self, subscription, event):
        try:
            membership = subscription.firm.members.select_related('user').first()
            if membership:
                track_event(
                    user=membership.user,
                    event_name="webhook_assinatura_atualizada",
                    properties={
                        "evento_abacatepay": event,
                        "subscription_id": subscription.id,
                        "novo_status": subscription.status,
                        "firm_id": subscription.firm.id,
                    },
                )
        except Exception:
            pass
