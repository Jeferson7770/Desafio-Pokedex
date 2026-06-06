
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('firms', '0002_alter_firm_type_alter_firmmember_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinancialReportSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ('year', models.IntegerField()),
                ('total_revenue', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('total_expense', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('expenses_fixed', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('expenses_variable', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('expenses_eventual', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('expenses_payroll', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, verbose_name='Pessoas/Folha')),
                ('expenses_taxes', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, verbose_name='Impostos')),
                ('expenses_structure', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, verbose_name='Estrutura/Escritório')),
                ('expenses_late_interest', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, verbose_name='Juros por Atraso')),
                ('team_size', models.IntegerField(default=0)),
                ('last_sync_at', models.DateTimeField(blank=True, null=True)),
                ('is_fully_categorized', models.BooleanField(default=False)),
                ('firm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_summaries', to='firms.firm')),
            ],
            options={
                'ordering': ['-year', '-month'],
                'unique_together': {('firm', 'month', 'year')},
            },
        ),
    ]
