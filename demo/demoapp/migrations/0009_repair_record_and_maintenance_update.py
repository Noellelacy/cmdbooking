from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0008_equipmentusage_quantity'),
    ]

    operations = [
        migrations.CreateModel(
            name='RepairRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issue_type', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('technician', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='demoapp.multimediaequipment')),
            ],
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='reported_by',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='resolution_notes',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='resolved_date',
        ),
        migrations.AddField(
            model_name='maintenancerecord',
            name='maintenance_type',
            field=models.CharField(default='General Maintenance', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='maintenancerecord',
            name='duration_hours',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='maintenancerecord',
            name='technician',
            field=models.CharField(default='Unknown', max_length=100),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='maintenancerecord',
            old_name='reported_date',
            new_name='date',
        ),
        migrations.RenameField(
            model_name='maintenancerecord',
            old_name='issue_description',
            new_name='description',
        ),
        migrations.AddField(
            model_name='maintenancerecord',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='maintenancerecord',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
