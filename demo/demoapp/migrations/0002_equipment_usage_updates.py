from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demoapp', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='equipmentusage',
            old_name='return_time',
            new_name='actual_return_time',
        ),
        migrations.AddField(
            model_name='equipmentusage',
            name='expected_return_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='equipmentusage',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('checked_out', 'Checked Out'), ('returned', 'Returned'), ('overdue', 'Overdue')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='equipmentusage',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_reservations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='equipmentusage',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='equipmentusage',
            name='approval_notes',
            field=models.TextField(blank=True),
        ),
    ]
