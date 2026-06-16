from django.db import migrations

CATEGORY_DEFAULT_PRIORITY = {
    "PESSOAL_E_REMUNERACAO": "CRITICA",
    "FISCAL_E_OBRIGACOES_LEGAIS": "CRITICA",
    "CUSTAS_PROCESSUAIS_E_JUDICIAIS": "ESPECIAL",
    "ESTRUTURA_E_OPERACAO": "ALTA",
    "TECNOLOGIA_E_ASSINATURA": "MEDIA_ALTA",
    "FINANCEIRA": "MEDIA",
    "MARKETING_E_AQUISICAO": "MEDIA",
    "MOBILIDADE_E_DESLOCAMENTO": "MEDIA_BAIXA",
    "INVESTIMENTOS_NO_ESCRITORIO": "BAIXA",
    "CAPACITACAO_E_DESENVOLVIMENTO": "BAIXA",
    "A_CLASSIFICAR": "INDEFINIDA",
}


def sync_forward(apps, schema_editor):
    Expense = apps.get_model("expenses", "Expense")
    for category, priority in CATEGORY_DEFAULT_PRIORITY.items():
        Expense.objects.filter(category=category).update(priority=priority)


def sync_reverse(apps, schema_editor):
    pass  # irreversível sem snapshot anterior


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0011_remap_legacy_priority_and_category"),
    ]

    operations = [
        migrations.RunPython(sync_forward, sync_reverse),
    ]
