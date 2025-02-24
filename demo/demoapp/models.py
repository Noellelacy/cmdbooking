from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    USER_TYPES = (
        ('student', 'Student'),
        ('faculty', 'Faculty'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')
    number = models.CharField(max_length=20, blank=True)  # Student/Faculty ID
    
    def is_faculty(self):
        return self.user_type == 'faculty'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

class EquipmentCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Equipment Categories"

class MultimediaEquipment(models.Model):
    EQUIPMENT_TYPES = (
        ('AUD', _('Audio Equipment')),
        ('VID', _('Video Equipment')),
        ('OTH', _('Other'))
    )
    
    CONDITION_CHOICES = (
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('needs_repair', 'Needs Repair'),
    )
    
    name = models.CharField(max_length=200)
    equipment_type = models.CharField(max_length=3, choices=EQUIPMENT_TYPES)
    category = models.ForeignKey(EquipmentCategory, on_delete=models.SET_NULL, null=True)
    serial_number = models.CharField(max_length=100, unique=True, default='TEMP-SN')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    inventory_number = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=100)
    description = models.TextField()
    is_available = models.BooleanField(default=True)
    max_reservation_hours = models.IntegerField(default=4)
    requires_training = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='equipment_added')
    last_maintained = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='equipment_modified')
    
    def __str__(self):
        return f"{self.name} ({self.get_equipment_type_display()})"
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Multimedia Equipment')
        verbose_name_plural = _('Multimedia Equipment')

class EquipmentUsage(models.Model):
    equipment = models.ForeignKey(MultimediaEquipment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    checkout_time = models.DateTimeField(auto_now_add=True)
    return_time = models.DateTimeField(null=True, blank=True)
    purpose = models.TextField()
    course_code = models.CharField(max_length=20, blank=True)
    condition_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.equipment.name} - {self.user.get_full_name()}"

    class Meta:
        verbose_name = _('Equipment Usage')
        verbose_name_plural = _('Equipment Usage')

class MaintenanceRecord(models.Model):
    equipment = models.ForeignKey(MultimediaEquipment, on_delete=models.CASCADE)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    issue_description = models.TextField()
    reported_date = models.DateTimeField(auto_now_add=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.equipment.name} - {self.reported_date.strftime('%Y-%m-%d')}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update the user profile."""
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'user_type': 'student', 'number': ''}
        )
