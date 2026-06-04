
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firms', '0002_alter_firm_type_alter_firmmember_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('abacatepay_product_id', models.CharField(help_text='ID do produto gerado no painel do AbacatePay', max_length=255, unique=True)),
                ('cycle', models.CharField(choices=[('WEEKLY', 'Semanal'), ('MONTHLY', 'Mensal'), ('SEMIANNUALLY', 'Semestral'), ('ANNUALLY', 'Anual')], default='MONTHLY', max_length=20)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='FirmSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abacatepay_billing_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pendente'), ('ACTIVE', 'Ativa'), ('EXPIRED', 'Expirada'), ('CANCELLED', 'Cancelada')], default='PENDING', max_length=20)),
                ('current_period_end', models.DateTimeField(blank=True, help_text='Data de expiração do ciclo atual', null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('firm', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='firms.firm')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='firms.plan')),
            ],
        ),
    ]
