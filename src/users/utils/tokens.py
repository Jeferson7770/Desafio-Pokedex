from rest_framework_simplejwt.tokens import RefreshToken


class FirmRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        membership = user.firm_memberships.values("firm_id", "firm__name").first()
        token["firm_id"] = membership["firm_id"] if membership else None
        token["firm_name"] = membership["firm__name"] if membership else None
        return token
