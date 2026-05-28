from rest_framework import serializers
from ..models.motor import SimulacaoPrioridade, ItemSimulacaoPrioridade

class ItemSimulacaoPrioridadeSerializer(serializers.ModelSerializer):
    expense_title = serializers.CharField(source="parcela.expense.title", read_only=True)
    category = serializers.CharField(source="parcela.expense.category", read_only=True)
    priority = serializers.CharField(source="parcela.expense.priority", read_only=True)
    due_date = serializers.DateField(source="parcela.due_date", read_only=True)

    class Meta:
        model = ItemSimulacaoPrioridade
        fields = [
            "id", "parcela", "expense_title", "category", "priority", 
            "due_date", "status_recomendacao", "amount_snapshot", "late_interest_snapshot"
        ]


class SimulacaoPrioridadeSerializer(serializers.ModelSerializer):
    pagamentos_recomendados = serializers.SerializerMethodField()
    pagamentos_nao_cobertos = serializers.SerializerMethodField()
    reference_period = serializers.SerializerMethodField()

    class Meta:
        model = SimulacaoPrioridade
        fields = [
            "id", "reference_period", "saldo_total_disponivel", 
            "saldo_restante_pos_pagamentos", "created_at",
            "pagamentos_recomendados", "pagamentos_nao_cobertos"
        ]

    def get_reference_period(self, obj):
        return obj.reference_date.strftime("%Y-%m")

    def get_pagamentos_recomendados(self, obj):
        itens = obj.items.filter(status_recomendacao="RECOMENDADO")
        return ItemSimulacaoPrioridadeSerializer(itens, many=True).data

    def get_pagamentos_nao_cobertos(self, obj):
        itens = obj.items.filter(status_recomendacao="NAO_COBERTO")
        return ItemSimulacaoPrioridadeSerializer(itens, many=True).data


class SalvarConfiguracaoQuerySerializer(serializers.Serializer):
    year = serializers.IntegerField(required=True, min_value=2000, max_value=2100)
    month = serializers.IntegerField(required=True, min_value=1, max_value=12)