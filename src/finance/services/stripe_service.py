import stripe
from decouple import config
from rest_framework.exceptions import ValidationError


class StripeService:
    def __init__(self):
        self.secret_key = config("STRIPE_SECRET_KEY")
        self.publishable_key = config("STRIPE_PUBLISHABLE_KEY")
        stripe.api_key = self.secret_key

    def listar_planos(self):
        try:
            prices = stripe.Price.list(
                active=True,
                type="recurring",
                expand=["data.product"],
                limit=100,
            )
        except stripe.StripeError as e:
            raise ValidationError({"detail": f"Falha ao listar planos na Stripe: {str(e)}"})

        _cycle_map = {
            "month": "MONTHLY",
            "year": "ANNUAL",
            "week": "WEEKLY",
            "day": "DAILY",
        }

        planos = []
        for price in prices.data:
            product = price.product
            if not isinstance(product, stripe.Product) or not product.active:
                continue

            interval = price.recurring.interval if price.recurring else None
            planos.append({
                "id": price.id,
                "name": product.name,
                "description": product.description,
                "price": price.unit_amount,
                "currency": price.currency.upper(),
                "cycle": _cycle_map.get(interval, interval.upper() if interval else None),
                "imageUrl": product.images[0] if product.images else None,
                "status": "ACTIVE" if price.active else "INACTIVE",
            })

        return planos

    def criar_checkout_session(self, stripe_price_id, firm_subscription_id, firm_id, plan_name, user_email):
        frontend_url = config("FRONTEND_URL", default="").rstrip("/")
        success_url = f"{frontend_url}/app/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{frontend_url}/app/payment/return"

        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": stripe_price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "firm_subscription_id": str(firm_subscription_id),
                    "firm_id": str(firm_id),
                    "plan_name": plan_name,
                    "user_email": user_email,
                },
            )
        except stripe.StripeError as e:
            raise ValidationError({"detail": f"Falha ao criar sessão de checkout na Stripe: {str(e)}"})

        return {
            "session_id": session.id,
            "checkout_url": session.url,
        }
