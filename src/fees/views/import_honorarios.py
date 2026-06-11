from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..serializers.honorarios import HonorarioSerializer
from ...users.utils.telemetry import track_event
from ...users.utils.firm_mixin import FirmMixin


class HonorarioImportView(FirmMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        items = request.data
        
        if not isinstance(items, list):
            track_event(
                user=request.user,
                event_name="honorarios_importacao_falha_estrutura",
                properties={"motivo_erro": "payload_nao_e_lista"}
            )
            return Response(
                {"detail": "Payload deve ser um array de objetos."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if len(items) > 500:
            track_event(
                user=request.user,
                event_name="honorarios_importacao_falha_estrutura",
                properties={
                    "quantidade_itens_tentados": len(items),
                    "motivo_erro": "limite_maximo_excedido"
                }
            )
            return Response(
                {"detail": "Máximo de 500 registros por importação."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        firm_id = self._get_firm_id()
        if not firm_id:
            track_event(
                user=request.user,
                event_name="honorarios_importacao_falha_estrutura",
                properties={"motivo_erro": "usuario_sem_empresa_vinculada"}
            )
            return Response(
                {"detail": "O usuário não possui nenhuma empresa vinculada para associar a importação."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        created_items = []
        error_items = []

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                error_items.append({
                    "index": index,
                    "detail": "Formato inválido de objeto dentro do array."
                })
                continue

            serializer = HonorarioSerializer(data=item)
            
            if serializer.is_valid():
                try:
                    honorario_instance = serializer.save(firm_id=firm_id)
                    created_items.append(HonorarioSerializer(honorario_instance).data)
                except Exception as e:
                    error_items.append({
                        "index": index,
                        "detail": f"Erro interno ao salvar registro: {str(e)}"
                    })
            else:
                first_field = next(iter(serializer.errors))
                first_error = serializer.errors[first_field][0]
                error_items.append({
                    "index": index,
                    "detail": f"{first_field}: {str(first_error)}"
                })

        track_event(
            user=request.user,
            event_name="honorarios_importacao_processada",
            properties={
                "total_itens_enviados": len(items),
                "sucessos_count": len(created_items),
                "falhas_count": len(error_items),
                "taxa_sucesso_percentual": (len(created_items) / len(items) * 100) if items else 0.0
            }
        )

        return Response(
            {
                "created": created_items,
                "errors": error_items
            },
            status=status.HTTP_200_OK
        )