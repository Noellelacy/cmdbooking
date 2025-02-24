import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demo.settings')
django.setup()

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

# Get the correct content type for auth.User
auth_user_ct = ContentType.objects.get(app_label='auth', model='user')

# Update all admin log entries to use the correct content type
LogEntry.objects.filter(content_type__model='user').update(content_type=auth_user_ct)

print("Fixed admin log entries")
