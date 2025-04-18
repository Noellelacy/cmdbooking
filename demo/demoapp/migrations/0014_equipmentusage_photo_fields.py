# Generated by Django 5.1.6 on 2025-03-23 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0013_fake_maintenancerecord_transition'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentusage',
            name='equipment_photo',
            field=models.ImageField(blank=True, null=True, upload_to='equipment_photos/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='equipmentusage',
            name='photo_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='equipmentusage',
            name='photo_uploaded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
