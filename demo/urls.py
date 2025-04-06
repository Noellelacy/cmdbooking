"""demo URL Configuration"""
from django.urls import path, re_path, include
from djreservation import urls as djreservation_urls
from demoapp import views
from demoapp.views import (
    home, signup, login_view, logout_view,
    my_reservations, equipment_return, dashboard,
    faculty_dashboard, equipment_list_manage, equipment_create,
    equipment_edit, equipment_delete, category_list, category_create,
    category_edit, category_delete, faculty_login, faculty_logout_view,
    report_maintenance, manage_reservations, approve_reservation, 
    reject_reservation, StudentEquipmentListView, mark_checked_out,
    mark_returned, refresh_csrf, faculty_analytics, equipment_detail_analytics,
    manage_blacklist, blacklist_student, remove_from_blacklist,
    upload_equipment_photo, review_equipment_photo, browse_equipment,
    maintenance_list, maintenance_create, maintenance_detail, maintenance_resolve,
    admin_student_management, admin_blacklist_student, admin_remove_blacklist, admin_bulk_blacklist
)
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from demoapp.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', home, name='home'),
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('refresh-csrf/', refresh_csrf, name='refresh_csrf'),
    path('equipment/', StudentEquipmentListView.as_view(), name='equipment_list'),
    path('browse/', browse_equipment, name='browse_equipment'),
    path('reservations/', my_reservations, name='my_reservations'),
    path('equipment/return/<int:usage_id>/', equipment_return, name='equipment_return'),
    path('dashboard/', dashboard, name='dashboard'),
    
    # Faculty URLs
    path('faculty/login/', faculty_login, name='faculty_login'),
    path('faculty/dashboard/', faculty_dashboard, name='faculty_dashboard'),
    path('faculty/analytics/', faculty_analytics, name='faculty_analytics'),
    path('faculty/equipment/<int:equipment_id>/analytics/', equipment_detail_analytics, name='equipment_detail_analytics'),
    path('faculty/logout/', faculty_logout_view, name='faculty_logout'),
    path('faculty/equipment/', equipment_list_manage, name='equipment_list_manage'),
    path('faculty/equipment/add/', equipment_create, name='equipment_create'),
    path('faculty/equipment/<int:pk>/edit/', equipment_edit, name='equipment_edit'),
    path('faculty/equipment/<int:pk>/delete/', equipment_delete, name='equipment_delete'),
    path('faculty/categories/', category_list, name='category_list'),
    path('faculty/categories/add/', category_create, name='category_create'),
    path('faculty/categories/<int:pk>/edit/', category_edit, name='category_edit'),
    path('faculty/categories/<int:pk>/delete/', category_delete, name='category_delete'),
    path('faculty/maintenance/report/', report_maintenance, name='report_maintenance'),
    path('faculty/reservations/', manage_reservations, name='manage_reservations'),
    path('faculty/reservations/<int:reservation_id>/approve/', approve_reservation, name='approve_reservation'),
    path('faculty/reservations/<int:reservation_id>/reject/', reject_reservation, name='reject_reservation'),
    path('faculty/reservations/<int:reservation_id>/checkout/', mark_checked_out, name='mark_checked_out'),
    path('faculty/reservations/<int:reservation_id>/return/', mark_returned, name='mark_returned'),
    
    # Blacklist Management URLs
    path('faculty/blacklist/', manage_blacklist, name='manage_blacklist'),
    path('faculty/blacklist/add/<int:student_id>/', blacklist_student, name='blacklist_student'),
    path('faculty/blacklist/remove/<int:blacklist_id>/', remove_from_blacklist, name='remove_from_blacklist'),
    
    # Maintenance Management URLs
    path('faculty/maintenance/', maintenance_list, name='maintenance_list'),
    path('faculty/maintenance/create/', maintenance_create, name='maintenance_create'),
    path('faculty/maintenance/<int:pk>/', maintenance_detail, name='maintenance_detail'),
    path('faculty/maintenance/<int:pk>/resolve/', maintenance_resolve, name='maintenance_resolve'),
    
    # Equipment Photo Upload URLs
    path('reservations/<int:reservation_id>/upload-photo/', upload_equipment_photo, name='upload_equipment_photo'),
    path('faculty/reservations/<int:reservation_id>/review-photo/', review_equipment_photo, name='review_equipment_photo'),
    
    # Cart URLs
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:equipment_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    
    # Admin Student Management for Blacklisting
    path('admin/students/', admin_student_management, name='admin_student_management'),
    path('admin/students/blacklist/', admin_blacklist_student, name='admin_blacklist_student'),
    path('admin/students/unblacklist/', admin_remove_blacklist, name='admin_remove_blacklist'),
    path('admin/students/bulk-blacklist/', admin_bulk_blacklist, name='admin_bulk_blacklist'),
    
    # CSRF
    path('csrf/refresh/', refresh_csrf, name='refresh_csrf'),
]

# Add these lines to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
