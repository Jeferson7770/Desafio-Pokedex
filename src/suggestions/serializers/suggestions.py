from rest_framework import serializers
from ..models.suggestions_structure import Suggestion

class SuggestionSerializer(serializers.ModelSerializer):
    category_display = serializers.SerializerMethodField()

    class Meta:
        model = Suggestion
        fields = [
            "id",
            "name",
            "email",
            "category",
            "category_display",
            "subject",
            "message",
            "created_at",
        ]

    def get_category_display(self, obj):
        return obj.get_category_display()