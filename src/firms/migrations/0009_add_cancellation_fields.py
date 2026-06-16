from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("firms", "0008_add_trial_to_subscription"),
    ]

    operations = [
        migrations.AddField(
            model_name="firmsubscription",
            name="cancel_reason",
            field=models.CharField(blank=True, help_text="Motivo selecionado no cancelamento", max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="firmsubscription",
            name="cancel_feedback",
            field=models.TextField(blank=True, help_text="Texto livre do cancelamento", null=True),
        ),
        migrations.AddField(
            model_name="firmsubscription",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, help_text="Quando o cancelamento foi solicitado", null=True),
        ),
    ]
