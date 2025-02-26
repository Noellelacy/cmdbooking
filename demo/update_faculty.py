from django.contrib.auth.models import User
from demoapp.models import UserProfile

# Update Faculty user's profile
faculty_user = User.objects.get(username='Faculty')
profile = faculty_user.userprofile
profile.user_type = 'faculty'
profile.save()

print(f"Updated {faculty_user.username}'s profile to faculty type")
