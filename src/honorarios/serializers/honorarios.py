from rest_framework import serializers
from ..models.honorarios import Honorario

class HonorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Honorario
        fields = ["id", "title", "amount", "date", "status", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]