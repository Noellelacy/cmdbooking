from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from demoapp.models import MultimediaEquipment, MaintenanceRecord, RepairRecord

class Command(BaseCommand):
    help = 'Adds sample maintenance and repair records for testing'

    def handle(self, *args, **kwargs):
        # Get all equipment
        equipment_list = MultimediaEquipment.objects.all()
        
        if not equipment_list:
            self.stdout.write(self.style.ERROR('No equipment found in database'))
            return

        maintenance_types = [
            'Routine Check',
            'Software Update',
            'Hardware Cleaning',
            'Calibration',
            'Battery Replacement',
            'Firmware Update'
        ]

        repair_types = [
            'Screen Repair',
            'Battery Replacement',
            'Port Repair',
            'Hardware Malfunction',
            'Software Issue',
            'Physical Damage'
        ]

        technicians = [
            'John Smith',
            'Maria Garcia',
            'David Chen',
            'Sarah Johnson',
            'Michael Brown'
        ]

        now = timezone.now()
        
        # Create maintenance records
        for equipment in equipment_list:
            # Add 3-5 maintenance records per equipment
            for _ in range(random.randint(3, 5)):
                date = now - timedelta(days=random.randint(1, 90))
                MaintenanceRecord.objects.create(
                    equipment=equipment,
                    maintenance_type=random.choice(maintenance_types),
                    description=f'Regular maintenance performed on {equipment.name}',
                    date=date,
                    duration_hours=random.uniform(0.5, 4.0),
                    technician=random.choice(technicians)
                )

            # Add 1-3 repair records per equipment
            for _ in range(random.randint(1, 3)):
                start_date = now - timedelta(days=random.randint(1, 90))
                repair_duration = timedelta(days=random.randint(1, 5))
                RepairRecord.objects.create(
                    equipment=equipment,
                    issue_type=random.choice(repair_types),
                    description=f'Repair needed for {equipment.name}',
                    start_date=start_date,
                    end_date=start_date + repair_duration,
                    cost=random.uniform(50.0, 500.0),
                    technician=random.choice(technicians)
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully added sample maintenance and repair records')
        )
