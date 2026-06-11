from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from ..utils.tokens import FirmRefreshToken
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from ..serializers.register import RegisterSerializer
from ..utils.telemetry import track_event


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='post')
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            refresh = FirmRefreshToken.for_user(user)

            track_event(
                user=user,
                event_name="usuario_cadastrado_sucesso",
                properties={
                    "origem": "api_cadastro_direto"
                }
            )

            return Response({
                "user": {
                    "id": user.id,
                    "email": user.email
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            })

        try:
            email_tentativa = request.data.get("email")
            if email_tentativa:
                from types import SimpleNamespace
                user_mock = SimpleNamespace(id=0, email=email_tentativa, is_anonymous=False)
                track_event(
                    user=user_mock,
                    event_name="usuario_cadastrado_falha",
                    properties={
                        "erros_validacao": serializer.errors
                    }
                )
        except Exception:
            pass

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)