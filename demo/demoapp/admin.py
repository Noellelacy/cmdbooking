from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import MultimediaEquipment, EquipmentUsage

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'get_number', 'date_joined', 'last_login', 'is_active')
    list_filter = ('is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    def get_number(self, obj):
        return obj.last_name  # Since we're storing the number in last_name field
    get_number.short_description = 'Number'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(MultimediaEquipment)
class MultimediaEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_type', 'inventory_number', 'location')
    list_filter = ('equipment_type', 'location', 'requires_training')
    search_fields = ('name', 'inventory_number', 'description')
    ordering = ('name', 'equipment_type')

@admin.register(EquipmentUsage)
class EquipmentUsageAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'user', 'checkout_time', 'return_time', 'course_code')
    list_filter = ('equipment__equipment_type', 'checkout_time', 'return_time')
    search_fields = ('equipment__name', 'user__username', 'user__first_name', 'user__last_name', 'course_code')
    ordering = ('-checkout_time',)