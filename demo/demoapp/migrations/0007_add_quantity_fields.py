from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0006_auto_20250226_2000'),
    ]

    operations = [
        migrations.AddField(
            model_name='multimediaequipment',
            name='total_quantity',
            field=models.IntegerField(default=1, help_text='Total number of this equipment available'),
        ),
        migrations.AddField(
            model_name='multimediaequipment',
            name='available_quantity',
            field=models.IntegerField(default=1, help_text='Current number available for reservation'),
        ),
        migrations.AddField(
            model_name='multimediaequipment',
            name='min_alert_threshold',
            field=models.IntegerField(default=1, help_text='Minimum threshold to show limited stock warning'),
        ),
    ]
