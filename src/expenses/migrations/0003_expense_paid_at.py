
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0002_expense_category_expense_is_paid_expense_priority_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='paid_at',
            field=models.DateField(blank=True, null=True, verbose_name='Data do Pagamento'),
        ),
    ]
