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
    category_edit, category_delete, faculty_login, faculty_logout_view
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
    
    # Admin URL
    path('admin/', admin.site.urls),
    
    # djreservation URLs
    re_path(r'^reservation/', include(djreservation_urls)),
]
