from rest_framework import serializers
from ..models.relatorios import FinancialReportSummary
from ..services.cashflow import CashFlowEngine

class FinancialReportDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer leve que consome as estruturas de dados validadas pelo
    CashFlowEngine, garantindo velocidade de entrega para o Front-end.
    """

    class Meta:
        model = FinancialReportSummary
        fields = '__all__'
        read_only_fields = ['firm']
    
    def to_representation(self, instance):
        engine = CashFlowEngine(instance)
        report_payload = engine.generate_full_report()
        
        return report_payload.to_dict()