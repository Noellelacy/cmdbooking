from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from demoapp.models import UserProfile

class Command(BaseCommand):
    help = 'Lists all users and their profiles'

    def handle(self, *args, **kwargs):
        users = User.objects.all().select_related('userprofile')
        
        self.stdout.write(self.style.SUCCESS('=== Users List ==='))
        for user in users:
            self.stdout.write(f'\nUsername: {user.username}')
            self.stdout.write(f'Full Name: {user.get_full_name()}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Is Staff: {user.is_staff}')
            self.stdout.write(f'Is Superuser: {user.is_superuser}')
            try:
                profile = user.userprofile
                self.stdout.write(f'User Type: {profile.user_type}')
                self.stdout.write(f'Number: {profile.number}')
            except UserProfile.DoesNotExist:
                self.stdout.write(self.style.WARNING('No profile found'))
