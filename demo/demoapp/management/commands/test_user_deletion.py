from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from demoapp.models import UserProfile

class Command(BaseCommand):
    help = 'Test user deletion functionality'

    def handle(self, *args, **kwargs):
        # Create a test user
        with transaction.atomic():
            test_user = User.objects.create_user(
                username='test_delete_user',
                password='test123',
                email='test@example.com'
            )
            self.stdout.write(f'Created test user: {test_user.username}')
            
            # Verify profile was created
            try:
                profile = test_user.userprofile
                self.stdout.write(f'UserProfile created automatically: {profile}')
            except UserProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR('Profile was not created!'))
                return
            
            # Try to delete the user
            try:
                test_user.delete()
                self.stdout.write(self.style.SUCCESS('Successfully deleted test user'))
                
                # Verify user is gone
                if not User.objects.filter(username='test_delete_user').exists():
                    self.stdout.write(self.style.SUCCESS('User no longer exists in database'))
                
                # Verify profile is gone
                if not UserProfile.objects.filter(user=test_user).exists():
                    self.stdout.write(self.style.SUCCESS('UserProfile was also deleted'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error deleting user: {str(e)}'))
