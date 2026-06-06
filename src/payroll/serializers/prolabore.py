from rest_framework import serializers
from ..models.prolabore import ProLaboreSimulation

class CenarioProLaboreSerializer(serializers.Serializer):
    pro_labore_bruto = serializers.FloatField()
    inss_socio = serializers.FloatField()
    liquido_socio = serializers.FloatField()
    inss_patronal = serializers.FloatField()
    custo_total_escritorio = serializers.FloatField()


class ProLaboreCalculoSerializer(serializers.Serializer):
    base_disponivel = serializers.FloatField()
    coef_variacao = serializers.FloatField()
    meses_analisados = serializers.IntegerField()
    nivel_recomendado = serializers.CharField()
    mensagem_alerta = serializers.CharField(allow_null=True)

    conservador = CenarioProLaboreSerializer()
    equilibrado = CenarioProLaboreSerializer()
    maximo_seguro = CenarioProLaboreSerializer()


class ProLaboreSimulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProLaboreSimulation
        fields = [
            "id", "perfil_estagio", "base_disponivel", "coef_variacao", 
            "meses_analisados", "pro_labore_sugerido", "custo_total_escritorio", "created_at"
        ]
        read_only_fields = ["id", "created_at"]