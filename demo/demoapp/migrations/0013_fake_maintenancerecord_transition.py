# Generated by Django 5.1.6 on 2025-03-23 22:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demoapp', '0012_check_maintenancerecord_fields'),
    ]

    operations = [
        # Add the reported_by field with a default value pointing to a superuser (first user)
        migrations.AddField(
            model_name='maintenancerecord',
            name='reported_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        # Rename created_at to reported_date if it exists
        migrations.RenameField(
            model_name='maintenancerecord',
            old_name='created_at',
            new_name='reported_date',
        ),
    ]
