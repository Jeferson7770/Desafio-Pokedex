from django.db import migrations


PRIORITY_MAP = {
    "LEGAL": "CRITICA",
    "OPCIONAL": "BAIXA",
    # OPERACIONAL → MEDIA (já tratado abaixo por exclusão de lista)
}

CATEGORY_MAP = {
    "PESSOAS": "PESSOAL_E_REMUNERACAO",
    "IMPOSTOS": "FISCAL_E_OBRIGACOES_LEGAIS",
    "ESTRUTURA": "ESTRUTURA_E_OPERACAO",
    "OPERACIONAL": "A_CLASSIFICAR",
}


def remap_forward(apps, schema_editor):
    Expense = apps.get_model("expenses", "Expense")

    for old, new in PRIORITY_MAP.items():
        Expense.objects.filter(priority=old).update(priority=new)

    # OPERACIONAL priority → MEDIA (não está no dict pois é palavra-chave reservada)
    Expense.objects.filter(priority="OPERACIONAL").update(priority="MEDIA")

    for old, new in CATEGORY_MAP.items():
        Expense.objects.filter(category=old).update(category=new)


def remap_reverse(apps, schema_editor):
    # Reversão aproximada — sem garantia de fidelidade total
    Expense = apps.get_model("expenses", "Expense")
    Expense.objects.filter(priority="CRITICA").update(priority="LEGAL")
    Expense.objects.filter(priority__in=["ALTA", "MEDIA_ALTA", "MEDIA", "ESPECIAL"]).update(priority="OPERACIONAL")
    Expense.objects.filter(priority__in=["MEDIA_BAIXA", "BAIXA", "INDEFINIDA"]).update(priority="OPCIONAL")


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0010_update_priority_and_category_choices"),
    ]

    operations = [
        migrations.RunPython(remap_forward, remap_reverse),
    ]
