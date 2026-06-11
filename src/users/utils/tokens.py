from rest_framework_simplejwt.tokens import RefreshToken


class FirmRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        firm_id = user.firm_memberships.values_list("firm_id", flat=True).first()
        token["firm_id"] = firm_id
        return token
