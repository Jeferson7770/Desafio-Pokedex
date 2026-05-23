from rest_framework import serializers
from ..services.cashflow import CashFlowEngine

class FinancialReportDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer leve que consome as estruturas de dados validadas pelo
    CashFlowEngine, garantindo velocidade de entrega para o Front-end.
    """
    
    def to_representation(self, instance):
        engine = CashFlowEngine(instance)
        report_payload = engine.generate_full_report()
        
        return report_payload.to_dict()