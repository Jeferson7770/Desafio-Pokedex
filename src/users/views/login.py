from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from ..serializers.login import LoginSerializer
from ..models.device import UserDevice

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)

            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            
            if 'iphone' in user_agent:
                device_name = "iPhone (Celular)"
            elif 'ipad' in user_agent:
                device_name = "iPad (Tablet)"
            elif 'android' in user_agent:
                device_name = "Dispositivo Android (Celular/Tablet)"
            elif 'macintosh' in user_agent or 'mac os' in user_agent:
                device_name = "Macintosh (Macbook/iMac)"
            elif 'windows' in user_agent:
                device_name = "Windows (Computador)"
            elif 'linux' in user_agent:
                device_name = "Linux (Computador)"
            else:
                device_name = "Dispositivo Desconhecido"

            if 'chrome' in user_agent and 'safari' in user_agent and 'edge' not in user_agent:
                browser = "Chrome"
            elif 'safari' in user_agent and 'chrome' not in user_agent:
                browser = "Safari"
            elif 'firefox' in user_agent:
                browser = "Firefox"
            elif 'edge' in user_agent or 'edg' in user_agent:
                browser = "Edge"
            else:
                browser = "Navegador Web"

            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip_address = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

            jti = refresh.get('jti')
            UserDevice.objects.update_or_create(
                user=user,
                refresh_token_id=jti,
                defaults={
                    "device_name": device_name,
                    "browser": browser,
                    "ip_address": ip_address
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