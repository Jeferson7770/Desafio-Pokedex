from rest_framework import serializers
from ..services.cashflow import CashFlowEngine

class FinancialReportDashboardSerializer(serializers.Serializer):
    """
    Serializer leve que consome as estruturas de dados validadas pelo
    CashFlowEngine, garantindo velocidade de entrega para o Front-end.
    """
    
    def to_representation(self, queryset):
        engine = CashFlowEngine(queryset)
        report_payload = engine.generate_full_report()
        
        return report_payload.to_dict()