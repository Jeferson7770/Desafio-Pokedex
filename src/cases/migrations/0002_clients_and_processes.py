# Generated manually for clients/processes module evolution.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Client",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("phone", models.CharField(blank=True, default="", max_length=20)),
                ("cpf_cnpj", models.CharField(blank=True, default="", max_length=18)),
                ("type", models.CharField(choices=[("PF", "Pessoa Fisica"), ("PJ", "Pessoa Juridica")], default="PF", max_length=2)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="clients", to="firms.firm")),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.RenameModel(
            old_name="Case",
            new_name="Process",
        ),
        migrations.AlterField(
            model_name="process",
            name="client_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="process",
            name="client",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="processes", to="cases.client"),
        ),
        migrations.AddField(
            model_name="process",
            name="status",
            field=models.CharField(choices=[("ATIVO", "Ativo"), ("CONCLUIDO", "Concluido")], default="ATIVO", max_length=20),
        ),
        migrations.AlterField(
            model_name="casepaymentschedule",
            name="case",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="schedules", to="cases.process"),
        ),
    ]
