# Generated by Django 5.1.6 on 2025-03-04 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0009_repair_record_and_maintenance_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='multimediaequipment',
            name='image',
            field=models.ImageField(blank=True, help_text='Upload an image of the equipment', null=True, upload_to='equipment_images/'),
        ),
    ]
