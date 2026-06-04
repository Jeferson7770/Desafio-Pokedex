
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_notificationsetting'),
    ]

    operations = [
        migrations.AddField(
            model_name='lawyerprofile',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
