from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from ..utils.tokens import FirmRefreshToken
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from ..serializers.login import LoginSerializer
from ..models.device import UserDevice
from ..utils.telemetry import track_event


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='post')
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data
            refresh = FirmRefreshToken.for_user(user)

            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            
            if 'iphone' in user_agent or ('os x' in user_agent and 'mobi' in user_agent):
                device_name = "iPhone (Celular)"
            elif 'ipad' in user_agent:
                device_name = "iPad (Tablet)"
            elif 'android' in user_agent:
                if 'mobi' in user_agent or 'touch' in user_agent:
                    device_name = "Android (Celular)"
                else:
                    device_name = "Android (Tablet)"
            elif 'macintosh' in user_agent or 'mac os' in user_agent:
                if 'mobi' in user_agent or 'touch' in user_agent:
                    device_name = "iPhone (Celular)"
                else:
                    device_name = "Macintosh (Macbook/iMac)"
            elif 'windows' in user_agent:
                if 'phone' in user_agent or 'mobi' in user_agent:
                    device_name = "Windows Phone (Celular)"
                else:
                    device_name = "Windows (Computador)"
            elif 'linux' in user_agent:
                device_name = "Linux (Computador)"
            else:
                device_name = "Dispositivo Desconhecido"

            if 'edge' in user_agent or 'edg' in user_agent:
                browser = "Edge"
            elif 'fxios' in user_agent or 'firefox' in user_agent:
                browser = "Firefox"
            elif 'crios' in user_agent or ('chrome' in user_agent and 'safari' in user_agent):
                browser = "Chrome"
            elif 'safari' in user_agent:
                browser = "Safari"
            else:
                browser = "Navegador Web"

            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')

            jti = refresh.get('jti')

            device_uuid = request.data.get("device_uuid")

            if device_uuid:
                UserDevice.objects.update_or_create(
                    user=user,
                    device_uuid=device_uuid,
                    defaults={
                        "device_name": device_name,
                        "browser": browser,
                        "ip_address": ip_address,
                        "refresh_token_id": jti
                    }
                )
            else:
                UserDevice.objects.update_or_create(
                    user=user,
                    device_name=device_name,
                    browser=browser,
                    defaults={
                        "ip_address": ip_address,
                        "refresh_token_id": jti
                    }
                )

            track_event(
                user=user,
                event_name="usuario_logou",
                properties={
                    "device_name": device_name,
                    "browser": browser,
                    "ip_address": ip_address,
                    "has_device_uuid": bool(device_uuid)
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

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)