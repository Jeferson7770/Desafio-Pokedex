from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from ..models.laywer import LawyerProfile
from ..models.device import UserDevice
from ..serializers.laywer import LawyerProfileSerializer
from ..utils.telemetry import track_event


class LawyerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = LawyerProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return LawyerProfile.objects.filter(user=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.first()
        if not obj:
            from django.http import Http404
            raise Http404("Nenhum perfil encontrado para o usuário autenticado.")
        
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not current_password or not new_password:
            track_event(
                user=user,
                event_name="alteracao_senha_falha",
                properties={"motivo_erro": "campos_obrigatorios_ausentes"}
            )
            raise ValidationError(
                {"detail": "Os campos 'current_password' e 'new_password' são obrigatórios."}
            )

        if not user.check_password(current_password):
            track_event(
                user=user,
                event_name="alteracao_senha_falha",
                properties={"motivo_erro": "senha_atual_incorreta"}
            )
            return Response(
                {"current_password": ["A senha atual está incorreta."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
        
        UserDevice.objects.filter(user=user).delete()

        refresh = RefreshToken.for_user(user)

        track_event(
            user=user,
            event_name="alteracao_senha_sucesso",
            properties={"deslogou_outros_dispositivos": True}
        )

        return Response(
            {
                "message": "Senha alterada com sucesso! Todos os outros dispositivos foram deslogados.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], url_path="disconnect-device/(?P<device_pk>[^/.]+)")
    def disconnect_device(self, request, device_pk=None):
        try:
            device = UserDevice.objects.get(pk=device_pk, user=request.user)
        except UserDevice.DoesNotExist:
            track_event(
                user=request.user,
                event_name="desconexao_dispositivo_falha",
                properties={"device_pk": device_pk, "motivo_erro": "dispositivo_nao_encontrado"}
            )
            raise ValidationError({"detail": "Dispositivo não encontrado ou já desconectado."})

        device_name = device.device_name
        browser = device.browser

        if device.refresh_token_id:
            try:
                token = OutstandingToken.objects.get(jti=device.refresh_token_id)
                BlacklistedToken.objects.get_or_create(token=token)
            except OutstandingToken.DoesNotExist:
                pass

        device.delete()

        track_event(
            user=request.user,
            event_name="desconexao_dispositivo_sucesso",
            properties={
                "device_pk": device_pk,
                "device_name": device_name,
                "browser": browser
            }
        )

        return Response(
            {"message": f"O dispositivo '{device_name}' foi desconectado com sucesso!"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], url_path="disconnect-all-devices")
    def disconnect_all_devices(self, request):
        user = request.user
        current_token_jti = request.auth.get("jti") if request.auth else None

        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            if current_token_jti and token.jti == current_token_jti:
                continue
            BlacklistedToken.objects.get_or_create(token=token)

        if current_token_jti:
            UserDevice.objects.filter(user=user).exclude(refresh_token_id=current_token_jti).delete()
        else:
            UserDevice.objects.filter(user=user).delete()

        track_event(
            user=user,
            event_name="desconexao_todos_dispositivos_sucesso"
        )

        return Response(
            {"detail": "Todos os outros dispositivos foram desconectados com sucesso."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["delete"], url_path="delete-account")
    def delete_account(self, request):
        user = request.user
        password = request.data.get("password")

        if not password:
            track_event(
                user=user,
                event_name="exclusao_conta_falha",
                properties={"motivo_erro": "senha_nao_fornecida"}
            )
            raise ValidationError({"password": ["A senha é obrigatória para confirmar a exclusão da conta."]})

        if not user.check_password(password):
            track_event(
                user=user,
                event_name="exclusao_conta_falha",
                properties={"motivo_erro": "senha_incorreta"}
            )
            return Response(
                {"password": ["Senha incorreta. A conta não foi excluída."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        memberships = user.firm_memberships.all()
        firms_to_check = [m.firm for m in memberships]

        user_id = user.id
        user_email = user.email

        from types import SimpleNamespace
        user_dump = SimpleNamespace(id=user_id, email=user_email, firm_memberships=user.firm_memberships)

        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        with transaction.atomic():
            user.delete()

            for firm in firms_to_check:
                if not firm.members.exists():
                    firm.delete()

        track_event(
            user=user_dump,
            event_name="usuario_excluiu_conta_sucesso",
            properties={
                "escritorios_verificados_count": len(firms_to_check)
            }
        )

        return Response(
            {"detail": "Sua conta e todos os dados associados foram excluídos permanentemente do nosso sistema."},
            status=status.HTTP_200_OK
        )