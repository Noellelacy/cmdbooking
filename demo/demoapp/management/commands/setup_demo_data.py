from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from demoapp.models import EquipmentCategory, MultimediaEquipment, UserProfile
from django.utils import timezone

class Command(BaseCommand):
    help = 'Sets up initial demo data for the reservation system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating initial data...')

        # Create categories
        categories = {
            'audio': EquipmentCategory.objects.create(
                name='Audio Equipment',
                description='Sound recording and playback equipment'
            ),
            'video': EquipmentCategory.objects.create(
                name='Video Equipment',
                description='Cameras, projectors, and video recording equipment'
            ),
            'computer': EquipmentCategory.objects.create(
                name='Computer Equipment',
                description='Laptops, tablets, and computing accessories'
            )
        }
        
        # Create faculty user
        faculty_user = User.objects.create_user(
            username='faculty1',
            email='faculty1@example.com',
            password='faculty123',
            first_name='John',
            last_name='Smith'
        )
        UserProfile.objects.create(
            user=faculty_user,
            user_type='faculty',
            number='FAC001'
        )

        # Create student user
        student_user = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='student123',
            first_name='Jane',
            last_name='Doe'
        )
        UserProfile.objects.create(
            user=student_user,
            user_type='student',
            number='STU001'
        )

        # Create equipment
        equipment_data = [
            {
                'name': 'Professional Microphone',
                'equipment_type': 'AUD',
                'category': categories['audio'],
                'serial_number': 'MIC001',
                'inventory_number': 'INV001',
                'location': 'Studio Room 101',
                'description': 'High-quality condenser microphone for professional audio recording',
                'condition': 'excellent',
                'max_reservation_hours': 48
            },
            {
                'name': '4K Video Camera',
                'equipment_type': 'VID',
                'category': categories['video'],
                'serial_number': 'CAM001',
                'inventory_number': 'INV002',
                'location': 'Media Lab 202',
                'description': 'Professional 4K video camera with advanced features',
                'condition': 'good',
                'max_reservation_hours': 72
            },
            {
                'name': 'MacBook Pro',
                'equipment_type': 'OTH',
                'category': categories['computer'],
                'serial_number': 'LAP001',
                'inventory_number': 'INV003',
                'location': 'Computer Lab 303',
                'description': 'MacBook Pro with video editing software',
                'condition': 'excellent',
                'max_reservation_hours': 24
            }
        ]

        for data in equipment_data:
            MultimediaEquipment.objects.create(**data)

        self.stdout.write(self.style.SUCCESS('Successfully created initial data'))
