
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motor', '0002_simulacaoprioridade_updated_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='itemsimulacaoprioridade',
            options={'ordering': ['ordem']},
        ),
        migrations.AddField(
            model_name='itemsimulacaoprioridade',
            name='ordem',
            field=models.PositiveIntegerField(default=0, help_text='Posição do card na tela'),
        ),
    ]
