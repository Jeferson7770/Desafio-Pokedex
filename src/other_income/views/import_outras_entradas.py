from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.outras_entradas import OutraEntradaSerializer


class OutraEntradaImportView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_user_firm(self, user):
        membership = user.firm_memberships.first()
        if not membership:
            return None
        return membership.firm

    def post(self, request):
        items = request.data

        if not isinstance(items, list):
            return Response(
                {"detail": "Payload deve ser um array de objetos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(items) > 500:
            return Response(
                {"detail": "Máximo de 500 registros por importação."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        firm = self._get_user_firm(request.user)
        if not firm:
            return Response(
                {"detail": "O usuário não possui nenhuma empresa vinculada para associar a importação."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_items = []
        error_items = []

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                error_items.append(
                    {
                        "index": index,
                        "detail": "Formato inválido de objeto dentro do array.",
                    }
                )
                continue

            serializer = OutraEntradaSerializer(data=item)

            if serializer.is_valid():
                try:
                    instance = serializer.save(firm=firm)
                    created_items.append(OutraEntradaSerializer(instance).data)
                except Exception as e:
                    error_items.append(
                        {
                            "index": index,
                            "detail": f"Erro interno ao salvar registro: {str(e)}",
                        }
                    )
            else:
                first_field = next(iter(serializer.errors))
                first_error = serializer.errors[first_field][0]
                error_items.append(
                    {
                        "index": index,
                        "detail": f"{first_field}: {str(first_error)}",
                    }
                )

        return Response(
            {
                "created": created_items,
                "errors": error_items,
            },
            status=status.HTTP_200_OK,
        )
