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
        return obj.userprofile.get_user_type_display() if hasattr(obj, 'userprofile') else 'No Profile'
    get_user_type.short_description = 'Role'
    get_user_type.admin_order_field = 'userprofile__user_type'

    def get_number(self, obj):
        return obj.userprofile.number if hasattr(obj, 'userprofile') else 'N/A'
    get_number.short_description = 'ID Number'
    get_number.admin_order_field = 'userprofile__number'

    def get_reservation_count(self, obj):
        count = EquipmentUsage.objects.filter(user=obj).count()
        url = reverse('admin:demoapp_equipmentusage_changelist') + f'?user__id__exact={obj.id}'
        return format_html('<a href="{}">{} reservations</a>', url, count)
    get_reservation_count.short_description = 'Reservations'

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
        usage = EquipmentUsage.objects.filter(equipment=obj, return_time__isnull=True).first()
        if usage:
            url = reverse('admin:auth_user_change', args=[usage.user.id])
            return format_html('<a href="{}">{}</a>', url, usage.user.username)
        return '-'
    get_current_user.short_description = 'Current User'

    def get_maintenance_status(self, obj):
        maintenance = MaintenanceRecord.objects.filter(equipment=obj, resolved_date__isnull=True).first()
        if maintenance:
            return format_html('<span style="color: red;">Maintenance Required</span>')
        return format_html('<span style="color: green;">OK</span>')
    get_maintenance_status.short_description = 'Maintenance'

@admin.register(EquipmentUsage)
class EquipmentUsageAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'user', 'get_user_type', 'checkout_time', 'return_time', 'get_status', 'course_code')
    list_filter = ('return_time', 'user__userprofile__user_type', 'equipment__equipment_type')
    search_fields = ('equipment__name', 'user__username', 'course_code')
    raw_id_fields = ('user', 'equipment')
    
    fieldsets = (
        ('Reservation Details', {
            'fields': (
                ('equipment', 'user'),
                ('checkout_time', 'return_time'),
                'course_code',
                'purpose'
            )
        }),
        ('Condition Notes', {
            'fields': ('condition_notes',),
            'classes': ('collapse',)
        })
    )

    def get_user_type(self, obj):
        return obj.user.userprofile.get_user_type_display()
    get_user_type.short_description = 'User Type'
    get_user_type.admin_order_field = 'user__userprofile__user_type'

    def get_status(self, obj):
        if obj.return_time:
            return format_html('<span style="color: green;">Returned</span>')
        if obj.checkout_time + timezone.timedelta(hours=obj.equipment.max_reservation_hours) < timezone.now():
            return format_html('<span style="color: red;">Overdue</span>')
        return format_html('<span style="color: orange;">Checked Out</span>')
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