import posthog


def track_system_event(event_name, properties=None):
    """Eventos de sistema sem usuário (ex: webhooks externos)."""
    if getattr(posthog, "disabled", False):
        return
    posthog.capture(
        distinct_id="system",
        event=event_name,
        properties=properties or {},
    )


def identify_user(user, extra_properties=None):
    """Associa user_id ao perfil no PostHog com nome e email. Chamar no cadastro."""
    if getattr(posthog, "disabled", False):
        return
    props = {
        "$email": user.email,
        "$name": (
            f"{user.first_name} {user.last_name}".strip()
            or user.first_name
            or user.email
        ),
    }
    if extra_properties:
        props.update(extra_properties)
    posthog.identify(distinct_id=str(user.id), properties=props)


def track_event(user, event_name, properties=None):
    if getattr(posthog, "disabled", False):
        return

    if not user or user.is_anonymous:
        return

    payload = {
        "user_email": user.email,
        "user_id": user.id,
    }

    if not hasattr(user, "_firm_telemetry_cache"):
        user._firm_telemetry_cache = (
            user.firm_memberships
            .values("firm_id", "firm__name")
            .first()
        )

    firm_data = user._firm_telemetry_cache
    if firm_data:
        payload["firm_id"] = str(firm_data["firm_id"])
        payload["firm_name"] = firm_data["firm__name"]

    if properties:
        payload.update(properties)

    posthog.capture(
        distinct_id=str(user.id),
        event=event_name,
        properties=payload
    )