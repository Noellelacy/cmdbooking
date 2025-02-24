from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from demoapp.models import UserProfile

class Command(BaseCommand):
    help = 'Creates missing user profiles for existing users'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            try:
                # Try to get the profile
                user.userprofile
            except UserProfile.DoesNotExist:
                # Create profile if it doesn't exist
                UserProfile.objects.create(user=user)
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} missing user profiles'
            )
        )
