from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from decimal import Decimal, InvalidOperation

from ..serializers.expenses import ExpenseSerializer
from ..models.expenses import Expense
from ...users.utils.telemetry import track_event

class ExpenseImportView(APIView):
    permission_classes = [IsAuthenticated]

    def _normalize_payload(self, item):
        normalized = dict(item)

        normalized["is_active"] = True

        if normalized.get("category") is None:
            normalized["category"] = Expense.Category.OPERACIONAL

        installment_value = normalized.get("installment_value")
        total_installments = normalized.get("total_installments", 1)

        if installment_value is not None:
            try:
                installment_value_decimal = Decimal(str(installment_value))
                total_installments_int = int(total_installments)
            except (InvalidOperation, ValueError, TypeError):
                raise ValueError("installment_value e total_installments devem ser numéricos válidos.")

            if total_installments_int < 1:
                raise ValueError("total_installments deve ser maior ou igual a 1.")

            expected_amount = (installment_value_decimal * total_installments_int).quantize(Decimal("0.01"))

            try:
                amount_decimal = Decimal(str(normalized.get("amount"))).quantize(Decimal("0.01"))
            except (InvalidOperation, TypeError):
                raise ValueError("amount deve ser um número válido.")

            if amount_decimal != expected_amount:
                raise ValueError("amount deve ser igual a installment_value * total_installments.")

            normalized["is_installment"] = total_installments_int >= 2

        return normalized

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
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if len(items) > 500:
            return Response(
                {"detail": "Máximo de 500 registros por importação."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        firm = self._get_user_firm(request.user)
        if not firm:
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

            try:
                normalized_item = self._normalize_payload(item)
            except ValueError as e:
                error_items.append({
                    "index": index,
                    "detail": str(e)
                })
                continue

            serializer = ExpenseSerializer(data=normalized_item)
            
            if serializer.is_valid():
                try:
                    expense_instance = serializer.save(firm=firm)
                    created_items.append(ExpenseSerializer(expense_instance).data)
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
            event_name="despesas_importadas",
            properties={
                "total_enviados": len(items),
                "total_criados": len(created_items),
                "total_erros": len(error_items),
            },
        )

        return Response(
            {
                "created": created_items,
                "errors": error_items
            },
            status=status.HTTP_200_OK
        )