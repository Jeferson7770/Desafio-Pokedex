from django.conf import settings
from django.db import transaction, IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from ..models.auth import User
from ..models.laywer import LawyerProfile
from ..validators.cpf import validate_cpf as validate_cpf_format
from ..utils.information_normalized import normalize_email, normalize_cpf


def _verify_google_id_token(token: str) -> dict:
    """Valida um ID Token do Google e retorna o payload (idinfo)."""
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        return idinfo
    except ValueError:
        raise serializers.ValidationError(
            {"id_token": ["Token do Google inválido ou expirado."]}
        )


class GoogleRegisterSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)
    cpf = serializers.CharField()
    oab_number = serializers.CharField()
    oab_state = serializers.CharField(max_length=2)
    device_uuid = serializers.CharField(required=False, allow_blank=True)

    def validate_cpf(self, value):
        value = normalize_cpf(value)
        value = validate_cpf_format(value)

        if LawyerProfile.objects.filter(cpf=value).exists():
            raise serializers.ValidationError("CPF já está cadastrado")

        return value

    def validate(self, data):
        idinfo = _verify_google_id_token(data["id_token"])

        if not idinfo.get("email_verified"):
            raise serializers.ValidationError(
                {"id_token": ["O email da conta Google não está verificado."]}
            )

        email = normalize_email(idinfo.get("email", ""))
        if not email:
            raise serializers.ValidationError(
                {"id_token": ["A conta Google não possui email associado."]}
            )

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": ["Este email já está cadastrado. Use o login com Google."]}
            )

        data["google_id"] = idinfo["sub"]
        data["email"] = email
        data["full_name"] = idinfo.get("name", "")
        return data

    def create(self, validated_data):
        try:
            with transaction.atomic():
                user = User(
                    email=validated_data["email"],
                    google_id=validated_data["google_id"],
                )
                user.set_unusable_password()
                user.save()

                LawyerProfile.objects.create(
                    user=user,
                    full_name=validated_data["full_name"],
                    cpf=normalize_cpf(validated_data["cpf"]),
                    oab_number=validated_data["oab_number"],
                    oab_state=validated_data["oab_state"],
                )

                return user

        except IntegrityError:
            raise ValidationError({"detail": "Email ou CPF já cadastrados"})


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)
    device_uuid = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        idinfo = _verify_google_id_token(data["id_token"])

        google_id = idinfo.get("sub")
        email = normalize_email(idinfo.get("email", ""))

        # Tenta encontrar pelo google_id primeiro, depois pelo email
        user = None
        try:
            user = User.objects.get(google_id=google_id)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=email)
                # Vincula o google_id à conta existente
                user.google_id = google_id
                user.save(update_fields=["google_id"])
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"detail": "Usuário não encontrado. Realize o cadastro primeiro."}
                )

        data["user"] = user
        return data
