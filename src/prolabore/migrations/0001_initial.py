
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProLaboreSimulation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('perfil_estagio', models.CharField(choices=[('INICIANTE', 'Iniciante'), ('INTERMEDIARIO', 'Intermediário'), ('AVANCADO', 'Avançado')], default='INTERMEDIARIO', max_length=20)),
                ('base_disponivel', models.DecimalField(decimal_places=2, max_digits=12)),
                ('coef_variacao', models.DecimalField(decimal_places=2, max_digits=5)),
                ('meses_analisados', models.PositiveIntegerField()),
                ('pro_labore_sugerido', models.DecimalField(decimal_places=2, max_digits=12)),
                ('custo_total_escritorio', models.DecimalField(decimal_places=2, max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pro_labore_simulations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
