from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import transaction

from ...finance.services.abacatepay import AbacatePayService
from ...firms.models.subscription import Plan, FirmSubscription
from ...users.utils.telemetry import track_event


class CriarAssinaturaView(APIView):
    permission_classes = [IsAuthenticated]

    LEGACY_INTERVAL_TO_CYCLE = {
        "ANNUAL": Plan.CycleType.ANNUALLY,
        "MONTHLY": Plan.CycleType.MONTHLY,
    }

    def _sync_plan_from_legacy_gateway_id(self, gateway_plan_id):
        """
        Compatibilidade com a modelagem antiga de billing em `src.users.models.billing`.
        Se encontrar o plano legado, cria/atualiza o plano equivalente em `firms.Plan`.
        """
        try:
            from ...users.models.billing import Plan as LegacyPlan
        except Exception:
            return None

        legacy_plan = LegacyPlan.objects.filter(
            gateway_plan_id=gateway_plan_id,
            is_active=True,
        ).first()
        if not legacy_plan:
            return None

        cycle = self.LEGACY_INTERVAL_TO_CYCLE.get(legacy_plan.interval, Plan.CycleType.MONTHLY)
        plan, _ = Plan.objects.update_or_create(
            abacatepay_product_id=gateway_plan_id,
            defaults={
                "name": legacy_plan.name,
                "price": legacy_plan.price,
                "cycle": cycle,
                "is_active": legacy_plan.is_active,
            },
        )
        return plan

    def _bootstrap_plan_from_gateway_product_id(self, gateway_product_id):
        """
        Quando o frontend manda apenas o product id do gateway (prod_*),
        garantimos um plano local minimo para viabilizar o fluxo de checkout.
        """
        plan, _ = Plan.objects.get_or_create(
            abacatepay_product_id=gateway_product_id,
            defaults={
                "name": f"Gateway {gateway_product_id[:40]}",
                "price": "0.00",
                "cycle": Plan.CycleType.MONTHLY,
                "is_active": True,
            },
        )
        return plan

    def _get_active_plan(self, plan_identifier):
        """
        Aceita tanto o ID numerico do plano quanto o ID textual do produto no gateway.
        """
        if plan_identifier is None:
            return None

        plan_identifier_str = str(plan_identifier).strip()
        if not plan_identifier_str:
            return None

        if plan_identifier_str.isdigit():
            plan = Plan.objects.filter(id=int(plan_identifier_str), is_active=True).first()
            if plan:
                return plan

            # Fallback: tenta resolver no modelo legado e sincronizar para firms.Plan.
            return self._sync_plan_from_legacy_gateway_id(plan_identifier_str)

        plan = Plan.objects.filter(abacatepay_product_id=plan_identifier_str, is_active=True).first()
        if plan:
            return plan

        # Fallback para bases antigas que ainda guardam plano em users.Plan.gateway_plan_id.
        return self._sync_plan_from_legacy_gateway_id(plan_identifier_str)

    def post(self, request):
        plan_id = request.data.get("plan_id")
        if not plan_id:
            track_event(
                user=request.user,
                event_name="assinatura_checkout_falha",
                properties={"motivo_erro": "plan_id nao fornecido"}
            )
            raise ValidationError({"plan_id": "Este campo é obrigatório para iniciar a assinatura."})

        plan_identifier = str(plan_id).strip()
        plan = self._get_active_plan(plan_identifier)
        if not plan and plan_identifier.startswith("prod_"):
            plan = self._bootstrap_plan_from_gateway_product_id(plan_identifier)

        if not plan:
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


class ListarPlanosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = AbacatePayService()
        produtos = service.listar_produtos()

        planos = [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "description": p.get("description"),
                "price": p.get("price"),          # centavos
                "currency": p.get("currency", "BRL"),
                "cycle": p.get("cycle"),
                "imageUrl": p.get("imageUrl"),
                "status": p.get("status"),
            }
            for p in produtos
        ]

        return Response({"data": planos}, status=status.HTTP_200_OK)