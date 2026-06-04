
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0003_expense_paid_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='frequency',
            field=models.CharField(choices=[('ONE_TIME', 'Única'), ('MONTHLY', 'Mensal'), ('ANNUAL', 'Anual')], default='ONE_TIME', max_length=20),
        ),
    ]
