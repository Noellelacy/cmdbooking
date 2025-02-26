from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from demoapp.models import UserProfile

class Command(BaseCommand):
    help = 'Check user profiles and their types'

    def handle(self, *args, **options):
        self.stdout.write("\nChecking User Profiles:")
        self.stdout.write("-" * 50)

        users = User.objects.all()
        for user in users:
            self.stdout.write(f"\nUser: {user.username}")
            self.stdout.write(f"Is staff: {user.is_staff}")
            self.stdout.write(f"Is superuser: {user.is_superuser}")
            try:
                profile = user.userprofile
                self.stdout.write(f"Profile type: {profile.user_type}")
                self.stdout.write(f"Is faculty: {profile.is_faculty()}")
            except UserProfile.DoesNotExist:
                self.stdout.write("No profile found!")
