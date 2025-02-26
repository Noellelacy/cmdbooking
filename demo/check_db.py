import sqlite3
import os

def print_tables(db_path):
    print(f"\nChecking database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"Row count: {count}")
    
    conn.close()

# Check both databases
root_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
demo_db = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

print("Root database:")
print_tables(root_db)
print("\nDemo database:")
print_tables(demo_db)
