from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from ..utils.telemetry import track_event


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            
            if request.user and not request.user.is_anonymous:
                track_event(
                    user=request.user,
                    event_name="usuario_deslogou",
                    properties={
                        "metodo": "token_blacklist"
                    }
                )

            token.blacklist()

            return Response({"detail": "Logout realizado com sucesso"})
        except Exception:
            return Response({"detail": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST)