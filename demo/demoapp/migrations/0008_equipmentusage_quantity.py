from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0007_add_quantity_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentusage',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
