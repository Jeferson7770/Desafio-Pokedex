class FirmMixin:
    """Reads firm_id from the JWT payload — zero DB queries for firm resolution.
    Falls back to a DB lookup for tokens issued before this claim was added.
    Also pre-populates _firm_telemetry_cache on the user so track_event()
    skips its DB query on all views that use this mixin."""

    def _get_firm_id(self):
        cached = getattr(self.request, "_firm_id_cache", None)
        if cached is not None:
            return cached

        auth = getattr(self.request, "auth", None)
        if auth is not None:
            payload = getattr(auth, "payload", {})
            firm_id = payload.get("firm_id")
            if firm_id is not None:
                self.request._firm_id_cache = firm_id
                if not hasattr(self.request.user, "_firm_telemetry_cache"):
                    self.request.user._firm_telemetry_cache = {
                        "firm_id": firm_id,
                        "firm__name": payload.get("firm_name"),
                    }
                return firm_id

        membership = self.request.user.firm_memberships.values("firm_id", "firm__name").first()
        self.request._firm_id_cache = membership["firm_id"] if membership else None
        if membership and not hasattr(self.request.user, "_firm_telemetry_cache"):
            self.request.user._firm_telemetry_cache = membership
        return self.request._firm_id_cache
