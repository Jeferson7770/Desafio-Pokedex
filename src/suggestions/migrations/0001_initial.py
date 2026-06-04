
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('firms', '0002_alter_firm_type_alter_firmmember_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='Suggestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('category', models.CharField(choices=[('MELHORIA', 'Melhoria de Funcionalidade'), ('NOVA_FUNC', 'Nova Funcionalidade'), ('BUG', 'Relato de Bug'), ('OUTRO', 'Outro')], default='MELHORIA', max_length=20)),
                ('subject', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('firm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suggestions', to='firms.firm')),
            ],
        ),
    ]
