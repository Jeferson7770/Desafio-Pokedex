class FirmMixin:
    """Reads firm_id from the JWT payload — zero DB queries for firm resolution.
    Falls back to a DB lookup for tokens issued before this claim was added."""

    def _get_firm_id(self):
        cached = getattr(self.request, "_firm_id_cache", None)
        if cached is not None:
            return cached

        auth = getattr(self.request, "auth", None)
        if auth is not None:
            firm_id = getattr(auth, "payload", {}).get("firm_id")
            if firm_id is not None:
                self.request._firm_id_cache = firm_id
                return firm_id

        firm_id = self.request.user.firm_memberships.values_list("firm_id", flat=True).first()
        self.request._firm_id_cache = firm_id
        return firm_id
