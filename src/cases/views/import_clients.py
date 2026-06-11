from collections import OrderedDict

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models.case_structure import Client
from ..serializers.case import ClientSerializer, ProcessSerializer
from ...users.utils.telemetry import track_event
from ...users.utils.firm_mixin import FirmMixin


class ClientImportView(FirmMixin, APIView):
    permission_classes = [IsAuthenticated]

    def _normalize_cpf_cnpj(self, value):
        if not value:
            return ""
        return "".join(ch for ch in str(value) if ch.isalnum())

    def _group_payload(self, items):
        grouped = OrderedDict()

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                grouped[f"__invalid__:{index}"] = {
                    "index": index,
                    "name": "",
                    "payload": item,
                    "invalid": True,
                }
                continue

            name = item.get("name", "")
            cpf_cnpj = self._normalize_cpf_cnpj(item.get("cpf_cnpj", ""))
            email = (item.get("email") or "").strip().lower()

            if cpf_cnpj:
                key = f"cpf:{cpf_cnpj}"
            elif email:
                key = f"email:{email}"
            else:
                key = f"idx:{index}"

            if key not in grouped:
                grouped[key] = {
                    "index": index,
                    "name": name,
                    "payload": {
                        "name": name,
                        "email": item.get("email", ""),
                        "phone": item.get("phone", ""),
                        "cpf_cnpj": item.get("cpf_cnpj", ""),
                        "type": item.get("type", "PF"),
                        "notes": item.get("notes", ""),
                        "processes": item.get("processes", []) or [],
                    },
                    "invalid": False,
                }
            else:
                processes = item.get("processes", []) or []
                grouped[key]["payload"]["processes"].extend(processes)

        return list(grouped.values())

    def _check_existing_duplicates(self, firm_id, payload):
        cpf_cnpj = self._normalize_cpf_cnpj(payload.get("cpf_cnpj", ""))
        email = (payload.get("email") or "").strip().lower()

        if cpf_cnpj:
            for existing in Client.objects.filter(firm_id=firm_id).values_list("cpf_cnpj", flat=True):
                if self._normalize_cpf_cnpj(existing) == cpf_cnpj:
                    return "CPF/CNPJ já cadastrado"

        if email and Client.objects.filter(firm_id=firm_id, email__iexact=email).exists():
            return "E-mail já cadastrado"

        return None

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

        firm_id = self._get_firm_id()
        if not firm_id:
            return Response(
                {"detail": "O usuário não possui nenhuma empresa vinculada para associar a importação."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_items = []
        error_items = []

        grouped_items = self._group_payload(items)

        for grouped in grouped_items:
            index = grouped["index"]
            name = grouped.get("name", "")

            if grouped.get("invalid"):
                error_items.append(
                    {
                        "index": index,
                        "name": name,
                        "detail": "Formato inválido de objeto dentro do array.",
                    }
                )
                continue

            payload = grouped["payload"]
            duplicate_error = self._check_existing_duplicates(firm_id, payload)
            if duplicate_error:
                error_items.append(
                    {
                        "index": index,
                        "name": payload.get("name", ""),
                        "detail": duplicate_error,
                    }
                )
                continue

            client_data = {
                "name": payload.get("name", ""),
                "email": payload.get("email", ""),
                "phone": payload.get("phone", ""),
                "cpf_cnpj": payload.get("cpf_cnpj", ""),
                "type": payload.get("type", "PF"),
                "notes": payload.get("notes", ""),
            }
            processes_data = payload.get("processes", []) or []

            try:
                with transaction.atomic():
                    client_serializer = ClientSerializer(data=client_data)
                    client_serializer.is_valid(raise_exception=True)
                    client = client_serializer.save(firm_id=firm_id)

                    created_processes = []
                    for process in processes_data:
                        process_payload = dict(process)
                        process_payload["client"] = client.id
                        process_payload["schedules"] = process_payload.get("schedules", []) or []

                        process_serializer = ProcessSerializer(
                            data=process_payload,
                            context={"request": request},
                        )
                        process_serializer.is_valid(raise_exception=True)
                        process_instance = process_serializer.save(firm_id=firm_id)
                        created_processes.append(ProcessSerializer(process_instance).data)

                    created_client = ClientSerializer(client).data
                    created_client["processes"] = created_processes
                    created_items.append(created_client)
            except Exception as e:
                error_items.append(
                    {
                        "index": index,
                        "name": payload.get("name", ""),
                        "detail": str(e),
                    }
                )

        track_event(
            user=request.user,
            event_name="clientes_importados",
            properties={
                "total_enviados": len(items),
                "total_criados": len(created_items),
                "total_erros": len(error_items),
            },
        )

        return Response(
            {
                "created": created_items,
                "errors": error_items,
            },
            status=status.HTTP_200_OK,
        )
