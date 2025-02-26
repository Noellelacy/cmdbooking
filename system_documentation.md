# Equipment Reservation System Documentation

## System Actors

### Student Actor
```
+------------------+
|     Student      |
+------------------+
Actions:
1. View Equipment
2. Make Reservations
3. View Own Reservations
4. Return Equipment
5. View Equipment Status
6. Update Profile
+------------------+
```

### Faculty Actor
```
+------------------+
|     Faculty      |
+------------------+
Actions:
1. Manage Equipment
   - Add Equipment
   - Edit Equipment
   - Delete Equipment
2. Manage Categories
   - Create Category
   - Edit Category
   - Delete Category
3. Manage Reservations
   - Approve/Reject
   - Mark Checked Out
   - Mark Returned
4. Report Maintenance
5. View All Reservations
6. Update Profile
+------------------+
```

## Class Diagram

### 1. UserProfile
```
+-------------------+
|    UserProfile    |
+-------------------+
| - user: OneToOne  |
| - user_type: str  |
| - number: str     |
+-------------------+
| + is_faculty()    |
| + __str__()      |
+-------------------+
```

### 2. EquipmentCategory
```
+----------------------+
|   EquipmentCategory  |
+----------------------+
| - name: str         |
| - description: text |
| - created_by: FK    |
| - created_at: date  |
+----------------------+
| + __str__()         |
+----------------------+
```

### 3. MultimediaEquipment
```
+---------------------------+
|    MultimediaEquipment    |
+---------------------------+
| - name: str              |
| - equipment_type: str    |
| - category: FK           |
| - serial_number: str     |
| - condition: str         |
| - inventory_number: str  |
| - location: str         |
| - description: text     |
| - is_available: bool    |
| - max_reservation_hrs: int|
| - requires_training: bool|
| - notes: text           |
| - added_by: FK          |
| - last_maintained: date |
| - created_at: date      |
| - updated_at: date      |
| - last_modified_by: FK  |
+---------------------------+
| + __str__()             |
| + save()                |
+---------------------------+
```

### 4. EquipmentUsage
```
+-------------------------+
|    EquipmentUsage      |
+-------------------------+
| - equipment: FK        |
| - user: FK            |
| - checkout_time: date  |
| - expected_return: date|
| - actual_return: date  |
| - course_code: str     |
| - purpose: text        |
| - condition_notes: text|
| - status: str         |
| - approved_by: FK     |
| - approved_at: date   |
| - approval_notes: text|
+-------------------------+
| + __str__()           |
| + is_overdue()        |
| + save()              |
+-------------------------+
```

### 5. MaintenanceRecord
```
+-------------------------+
|   MaintenanceRecord    |
+-------------------------+
| - equipment: FK        |
| - reported_by: FK      |
| - issue_description: text|
| - reported_date: date  |
| - resolved_date: date  |
| - resolution_notes: text|
+-------------------------+
| + __str__()           |
+-------------------------+
```

## ER Diagram
```
+---------------+     +----------------+     +-------------------+
|     User      |     |  UserProfile   |     |  EquipmentUsage   |
+---------------+     +----------------+     +-------------------+
| id (PK)      |---->| user_id (PK/FK)|     | id (PK)          |
| username      |     | user_type      |     | equipment_id (FK) |
| password      |     | number         |     | user_id (FK)      |
| email        |     |                |     | checkout_time     |
| first_name   |     |                |     | return_time       |
| last_name    |     |                |     | status            |
+---------------+     +----------------+     | approved_by (FK)  |
                                           +-------------------+
                                                    |
                                                    |
+------------------+     +-----------------+        |
| EquipmentCategory|     |MultimediaEquip. |        |
+------------------+     +-----------------+        |
| id (PK)         |     | id (PK)        |<-------+
| name            |<----| category_id (FK)|
| description     |     | name            |
| created_by (FK) |     | serial_number   |
+------------------+     | condition       |
                        | location        |
                        | is_available    |
                        +-----------------+
                                |
                                |
                        +------------------+
                        | MaintenanceRecord|
                        +------------------+
                        | id (PK)         |
                        | equipment_id (FK)|
                        | reported_by (FK) |
                        | description      |
                        | resolved_date    |
                        +------------------+
```

## Relationships

### Class Relationships
1. UserProfile ←→ User (One-to-One)
2. EquipmentCategory → User (Many-to-One)
3. MultimediaEquipment → EquipmentCategory (Many-to-One)
4. MultimediaEquipment → User (Many-to-One, twice: added_by, last_modified_by)
5. EquipmentUsage → MultimediaEquipment (Many-to-One)
6. EquipmentUsage → User (Many-to-One, twice: user, approved_by)
7. MaintenanceRecord → MultimediaEquipment (Many-to-One)
8. MaintenanceRecord → User (Many-to-One: reported_by)

### Actor Relationships
1. User (Student/Faculty) → UserProfile (1:1)
2. Student → EquipmentUsage (1:M)
3. Faculty → EquipmentCategory (1:M via created_by)
4. Faculty → MultimediaEquipment (1:M via added_by)
5. Faculty → EquipmentUsage (1:M via approved_by)
6. Faculty → MaintenanceRecord (1:M via reported_by)

## Template Structure
1. Authentication templates (`auth/`)
   - login.html
   - signup.html
   - faculty_login.html

2. Faculty-specific templates (`faculty/`)
   - Equipment management
   - Category management
   - Bulk operations

3. Student-specific templates (`student/`)
   - Equipment viewing
   - Reservation management

4. Shared templates (root directory)
   - base.html
   - index.html

## Key Points
- Students can only view and reserve equipment
- Faculty can manage all aspects of the system
- Both actors inherit from the base User model
- UserProfile distinguishes between Student and Faculty
- Faculty has additional permissions and access to management functions
