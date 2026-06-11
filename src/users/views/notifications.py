from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..models.notifications import NotificationSetting
from ..serializers.notifications import NotificationSettingSerializer
from ..utils.telemetry import track_event


class NotificationSettingViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSettingSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return NotificationSetting.objects.filter(user=self.request.user)

    def get_object(self):
        obj, created = NotificationSetting.objects.get_or_create(user=self.request.user)
        return obj

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_update(self, serializer):
        instance = serializer.save()
        track_event(
            user=self.request.user,
            event_name="notificacoes_configuracoes_atualizadas",
            properties={
                field: getattr(instance, field)
                for field in serializer.validated_data
            },
        )