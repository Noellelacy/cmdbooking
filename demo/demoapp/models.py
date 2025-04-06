from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import os
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
    
    # New quantity fields
    total_quantity = models.IntegerField(default=1, help_text="Total number of this equipment available")
    available_quantity = models.IntegerField(default=1, help_text="Current number available for reservation")
    min_alert_threshold = models.IntegerField(default=1, help_text="Minimum threshold to show limited stock warning")
    
    # Equipment image field
    image = models.ImageField(upload_to='equipment_images/', blank=True, null=True, help_text="Upload an image of the equipment")
    
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
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('pending_photo', 'Photo Required'),
        ('photo_submitted', 'Photo Submitted'),
        ('rejected', 'Rejected'),
        ('checked_out', 'Checked Out'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue')
    ]
    
    equipment = models.ForeignKey(MultimediaEquipment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    checkout_time = models.DateTimeField()
    expected_return_time = models.DateTimeField()
    actual_return_time = models.DateTimeField(null=True, blank=True)
    course_code = models.CharField(max_length=20, blank=True)
    purpose = models.TextField()
    condition_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reservations')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    equipment_photo = models.ImageField(upload_to='equipment_photos/%Y/%m/%d/', blank=True, null=True)
    photo_uploaded_at = models.DateTimeField(null=True, blank=True)
    photo_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.equipment.name} (x{self.quantity}) - {self.user.username} ({self.checkout_time})"
    
    def is_overdue(self):
        if self.actual_return_time:
            return self.actual_return_time > self.expected_return_time
        return timezone.now() > self.expected_return_time
    
    def save(self, *args, **kwargs):
        if self.is_overdue() and self.status in ['checked_out', 'approved']:
            self.status = 'overdue'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Equipment Usage')
        verbose_name_plural = _('Equipment Usage')
        ordering = ['-checkout_time']

class MaintenanceRecord(models.Model):
    equipment = models.ForeignKey(MultimediaEquipment, on_delete=models.CASCADE)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    issue_description = models.TextField()
    reported_date = models.DateTimeField(auto_now_add=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.equipment.name} - {self.reported_date.strftime('%Y-%m-%d')}"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    equipment = models.ForeignKey(MultimediaEquipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    purpose = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'equipment')
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.equipment.name} x{self.quantity}"
        
    def duration_hours(self):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 3600
        return 0

class BlacklistedStudent(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blacklist_records')
    blacklisted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blacklisted_students')
    reason = models.TextField()
    blacklisted_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    removed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='removed_blacklists')
    removed_date = models.DateTimeField(null=True, blank=True)
    removal_notes = models.TextField(blank=True)
    
    def __str__(self):
        status = "Active" if self.is_active else "Removed"
        return f"{self.student.username} - {status} - {self.blacklisted_date.strftime('%Y-%m-%d')}"
    
    class Meta:
        verbose_name = _('Blacklisted Student')
        verbose_name_plural = _('Blacklisted Students')
        ordering = ['-blacklisted_date']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for every new user"""
    if created:
        try:
            # Only create if it doesn't exist
            UserProfile.objects.get_or_create(
                user=instance,
                defaults={'user_type': 'student'}  # Default to student type
            )
        except Exception:
            pass

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    try:
        # Only save if profile exists, don't create new ones here
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
    except UserProfile.DoesNotExist:
        pass  # Don't create profile here, let create_user_profile handle it
