from django.db import migrations

def fix_user_references(apps, schema_editor):
    # Get the historical models
    ContentType = apps.get_model('contenttypes', 'ContentType')
    LogEntry = apps.get_model('admin', 'LogEntry')
    User = apps.get_model('auth', 'User')

    # Update content type references
    try:
        old_ct = ContentType.objects.filter(app_label='demoapp', model='user').first()
        if old_ct:
            # Get the auth.User content type
            auth_ct = ContentType.objects.get(app_label='auth', model='user')
            
            # Update LogEntry references
            LogEntry.objects.filter(content_type=old_ct).update(content_type=auth_ct)
            
            # Delete the old content type
            old_ct.delete()
    except:
        pass

class Migration(migrations.Migration):
    dependencies = [
        ('demoapp', '0002_remove_multimediaequipment_quantity_available_and_more'),
        ('admin', '0003_logentry_add_action_flag_choices'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(fix_user_references),
    ]
