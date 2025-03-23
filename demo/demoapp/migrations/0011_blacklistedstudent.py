from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demoapp', '0010_multimediaequipment_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlacklistedStudent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField()),
                ('blacklisted_date', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('removed_date', models.DateTimeField(blank=True, null=True)),
                ('removal_notes', models.TextField(blank=True)),
                ('blacklisted_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blacklisted_students', to=settings.AUTH_USER_MODEL)),
                ('removed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='removed_blacklists', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blacklist_records', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
