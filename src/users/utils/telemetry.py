import posthog

def track_event(user, event_name, properties=None):
    """
    Envia eventos customizados para o PostHog amarrando o Usuário e a Firma (Escritório).
    """
    if getattr(posthog, "disabled", False):
        return

    if not user or user.is_anonymous:
        return

    payload = {
        "user_email": user.email,
        "user_id": user.id,
    }

    membership = getattr(user, "firm_memberships", None)
    if membership and membership.exists():
        firm = membership.first().firm
        payload["firm_id"] = str(firm.id)
        payload["firm_name"] = firm.name

    if properties:
        payload.update(properties)

    posthog.capture(
        distinct_id=str(user.id),
        event=event_name,
        properties=payload
    )