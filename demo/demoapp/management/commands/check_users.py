from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry
from demoapp.models import UserProfile

class Command(BaseCommand):
    help = 'Detailed check of users and related data'

    def handle(self, *args, **kwargs):
        # Count users
        total_users = User.objects.count()
        self.stdout.write(f'\nTotal Users in auth_user table: {total_users}')
        
        # List all users with details
        self.stdout.write('\nDetailed User List:')
        self.stdout.write('=' * 50)
        
        for user in User.objects.all():
            self.stdout.write(f'\nUser ID: {user.id}')
            self.stdout.write(f'Username: {user.username}')
            self.stdout.write(f'Date joined: {user.date_joined}')
            
            # Check if user has profile
            try:
                profile = user.userprofile
                self.stdout.write(f'Profile: Yes (Type: {profile.user_type})')
            except UserProfile.DoesNotExist:
                self.stdout.write('Profile: No')
                
            # Check admin log entries
            log_entries = LogEntry.objects.filter(user=user).count()
            self.stdout.write(f'Admin Log Entries: {log_entries}')
            
        # Count profiles
        total_profiles = UserProfile.objects.count()
        self.stdout.write(f'\nTotal UserProfiles: {total_profiles}')
