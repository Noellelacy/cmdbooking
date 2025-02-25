from django.urls import path
from . import views

app_name = 'demoapp'

urlpatterns = [
    # Authentication URLs
    path('signup/', views.signup, name='signup'),
    path('faculty/login/', views.faculty_login, name='faculty_login'),
    path('student/login/', views.student_login, name='student_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Equipment Management URLs
    path('equipment/add/', views.add_equipment, name='add_equipment'),
    path('equipment/list/', views.StudentEquipmentListView.as_view(), name='equipment_list'),
    path('equipment/<int:pk>/reserve/', views.reserve_equipment, name='reserve_equipment'),
    
    # Dashboard URLs
    path('faculty/dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Reservation URLs
    path('my-reservations/', views.my_reservations, name='my_reservations'),
]
