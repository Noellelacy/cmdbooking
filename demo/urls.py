"""demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from djreservation import urls as djreservation_urls
from demoapp.views import (
    home, EquipmentReservation, signup, login_view, logout_view,
    equipment_list, my_reservations, equipment_return, dashboard,
    faculty_dashboard, equipment_list_manage, equipment_create,
    equipment_edit, equipment_delete, category_list, category_create,
    category_edit, category_delete, faculty_login, faculty_logout_view,
    report_maintenance, manage_reservations, approve_reservation, 
    reject_reservation, StudentEquipmentListView, mark_checked_out,
    mark_returned
)
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', home, name='home'),
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('equipment/', equipment_list, name='equipment_list'),
    path('reservations/', my_reservations, name='my_reservations'),
    path('equipment/return/<int:usage_id>/', equipment_return, name='equipment_return'),
    path('dashboard/', dashboard, name='dashboard'),
    
    # Faculty URLs
    path('faculty/login/', faculty_login, name='faculty_login'),
    path('faculty/dashboard/', faculty_dashboard, name='faculty_dashboard'),
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
    
    # Student URLs
    path('student/equipment/', StudentEquipmentListView.as_view(), name='student_equipment_list'),
    
    # Admin
    path('admin/', admin.site.urls),
    path('djreservation/', include(djreservation_urls)),
]
