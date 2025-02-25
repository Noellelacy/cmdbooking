from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    MultimediaEquipment, EquipmentUsage, UserProfile, 
    EquipmentCategory, MaintenanceRecord
)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fieldsets = (
        ('User Information', {
            'fields': ('user_type', 'number'),
            'description': 'Specify whether this user is a student or faculty member.'
        }),
    )
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        form.base_fields['user_type'].initial = 'faculty'  # Set default to faculty for admin interface
        return formset

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'get_user_type', 'get_number', 'email', 'get_reservation_count', 'is_active')
    list_filter = ('userprofile__user_type', 'is_active', 'last_login')
    search_fields = ('username', 'email', 'userprofile__number')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Status', {'fields': ('is_active',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def get_user_type(self, obj):
        try:
            return obj.userprofile.get_user_type_display()
        except UserProfile.DoesNotExist:
            return 'N/A'
    get_user_type.short_description = 'Role'
    get_user_type.admin_order_field = 'userprofile__user_type'

    def get_number(self, obj):
        try:
            return obj.userprofile.number
        except UserProfile.DoesNotExist:
            return 'N/A'
    get_number.short_description = 'ID Number'
    get_number.admin_order_field = 'userprofile__number'

    def get_reservation_count(self, obj):
        count = EquipmentUsage.objects.filter(user=obj).count()
        url = reverse('admin:demoapp_equipmentusage_changelist') + f'?user__id__exact={obj.id}'
        return format_html('<a href="{}">{} reservations</a>', url, count)
    get_reservation_count.short_description = 'Reservations'

    def save_model(self, request, obj, form, change):
        creating = not obj.pk  # Check if this is a new user
        super().save_model(request, obj, form, change)
        if creating:
            # Create profile for new users
            UserProfile.objects.get_or_create(
                user=obj,
                defaults={'user_type': 'student', 'number': ''}
            )

class MaintenanceRecordInline(admin.TabularInline):
    model = MaintenanceRecord
    extra = 0
    readonly_fields = ('reported_date',)
    fields = ('issue_description', 'reported_date', 'resolved_date', 'resolution_notes')
    can_delete = True

@admin.register(MultimediaEquipment)
class MultimediaEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_type', 'get_status', 'location', 'get_current_user', 'get_maintenance_status')
    list_filter = ('equipment_type', 'is_available', 'condition', 'category', 'requires_training')
    search_fields = ('name', 'inventory_number', 'serial_number')
    readonly_fields = ('created_at', 'updated_at', 'last_modified_by')
    inlines = [MaintenanceRecordInline]
    
    fieldsets = (
        ('Equipment Details', {
            'fields': (
                'name', 'equipment_type', 'category',
                ('inventory_number', 'serial_number'),
                'description'
            )
        }),
        ('Location & Status', {
            'fields': (
                'location',
                ('is_available', 'condition'),
                'requires_training'
            )
        }),
        ('Maintenance', {
            'fields': (
                'notes',
                ('created_at', 'updated_at'),
                'last_maintained'
            ),
            'classes': ('collapse',)
        })
    )

    def get_status(self, obj):
        if not obj.is_available:
            usage = EquipmentUsage.objects.filter(equipment=obj, return_time__isnull=True).first()
            if usage:
                return format_html(
                    '<span style="color: red;">In Use (until {})</span>',
                    usage.checkout_time + timezone.timedelta(hours=obj.max_reservation_hours)
                )
        return format_html(
            '<span style="color: green;">Available</span>' if obj.is_available 
            else '<span style="color: orange;">Unavailable</span>'
        )
    get_status.short_description = 'Status'

    def get_current_user(self, obj):
        """Get the current user of the equipment."""
        usage = EquipmentUsage.objects.filter(
            equipment=obj,
            status__in=['checked_out', 'overdue']
        ).first()
        if usage:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:auth_user_change', args=[usage.user.id]),
                usage.user.get_full_name() or usage.user.username
            )
        return '-'
    get_current_user.short_description = 'Current User'

    def get_maintenance_status(self, obj):
        """Get the maintenance status of the equipment."""
        usage = EquipmentUsage.objects.filter(
            equipment=obj,
            status__in=['checked_out', 'overdue']
        ).first()
        if usage and usage.is_overdue():
            return format_html('<span style="color: red;">Overdue</span>')
        return format_html('<span style="color: green;">OK</span>')
    get_maintenance_status.short_description = 'Maintenance'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new equipment
            obj.added_by = request.user
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(EquipmentUsage)
class EquipmentUsageAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'user', 'get_user_type', 'checkout_time', 'actual_return_time', 'get_status', 'course_code')
    list_filter = ('status', 'user__userprofile__user_type', 'equipment__equipment_type', 'checkout_time', 'actual_return_time')
    search_fields = ('equipment__name', 'user__username', 'course_code')
    raw_id_fields = ('user', 'equipment')
    
    fieldsets = (
        ('Reservation Details', {
            'fields': (
                ('equipment', 'user'),
                ('checkout_time', 'expected_return_time', 'actual_return_time'),
                'course_code',
                'purpose',
                'status'
            )
        }),
        ('Approval Details', {
            'fields': (
                'approved_by',
                'approved_at',
                'approval_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Condition Notes', {
            'fields': ('condition_notes',),
            'classes': ('collapse',)
        })
    )

    def get_user_type(self, obj):
        try:
            return obj.user.userprofile.get_user_type_display()
        except:
            return 'N/A'
    get_user_type.short_description = 'User Type'
    get_user_type.admin_order_field = 'user__userprofile__user_type'

    def get_status(self, obj):
        status_colors = {
            'pending': 'orange',
            'approved': 'blue',
            'rejected': 'red',
            'checked_out': 'purple',
            'returned': 'green',
            'overdue': 'darkred'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">{}</span>', 
                         color, obj.get_status_display())
    get_status.short_description = 'Status'

@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_equipment_count', 'created_at')
    search_fields = ('name', 'description')
    
    def get_equipment_count(self, obj):
        count = MultimediaEquipment.objects.filter(category=obj).count()
        url = reverse('admin:demoapp_multimediaequipment_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} items</a>', url, count)
    get_equipment_count.short_description = 'Equipment Count'

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'issue_description', 'reported_date', 'get_status', 'get_duration')
    list_filter = ('resolved_date', 'reported_date')
    search_fields = ('equipment__name', 'issue_description')
    raw_id_fields = ('equipment',)
    
    def get_status(self, obj):
        if obj.resolved_date:
            return format_html('<span style="color: green;">Resolved</span>')
        return format_html('<span style="color: red;">Pending</span>')
    get_status.short_description = 'Status'
    
    def get_duration(self, obj):
        if obj.resolved_date:
            duration = obj.resolved_date - obj.reported_date
            return f'{duration.days} days'
        duration = timezone.now() - obj.reported_date
        return format_html('<span style="color: orange;">{} days (ongoing)</span>', duration.days)
    get_duration.short_description = 'Duration'

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)