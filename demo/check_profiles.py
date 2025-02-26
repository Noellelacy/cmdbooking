from django.contrib.auth.models import User
from demoapp.models import UserProfile

print("\nChecking User Profiles:")
print("-" * 50)

users = User.objects.all()
for user in users:
    print(f"\nUser: {user.username}")
    print(f"Is staff: {user.is_staff}")
    print(f"Is superuser: {user.is_superuser}")
    try:
        profile = user.userprofile
        print(f"Profile type: {profile.user_type}")
        print(f"Is faculty: {profile.is_faculty()}")
    except UserProfile.DoesNotExist:
        print("No profile found!")
