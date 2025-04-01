#!/usr/bin/env python
"""
Script to migrate data from local SQLite database to PostgreSQL on Render
Run this from your Django project root directory
"""

import os
import sys
import django
import psycopg2
import sqlite3
import json
from datetime import datetime, date
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facial_recognition_api.settings')
django.setup()

from django.conf import settings

# PostgreSQL connection details - get from .env file
POSTGRES_URL = os.environ.get('DATABASE_URL')
if not POSTGRES_URL:
    POSTGRES_URL = input("Enter your PostgreSQL database URL from Render: ")

print(f"Using database URL: {POSTGRES_URL}")

# Tables to migrate - add all your tables here
TABLES_TO_MIGRATE = [
    'users_user', 
    'users_student', 
    'users_admin', 
    'recognition_recognitionlog',
    'auth_permission',
    'django_content_type',
    'auth_group',
    'auth_group_permissions',
    'users_user_groups',
    'users_user_user_permissions',
    'django_admin_log',
    'django_session'
]

# Get SQLite database path - explicitly set path to local SQLite database
# sqlite_db_path = settings.DATABASES['default']['NAME']  # This is now pointing to PostgreSQL
sqlite_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
print(f"SQLite database path: {sqlite_db_path}")

if not os.path.exists(sqlite_db_path):
    print(f"Error: SQLite database file not found at {sqlite_db_path}")
    alternative_path = input("Enter the correct path to your SQLite database file: ")
    if alternative_path and os.path.exists(alternative_path):
        sqlite_db_path = alternative_path
    else:
        print("No valid SQLite database file provided. Exiting.")
        sys.exit(1)

if sqlite_db_path == ':memory:':
    print("SQLite database is in-memory, cannot migrate")
    sys.exit(1)

def sqlite_connect():
    """Connect to the SQLite database"""
    return sqlite3.connect(sqlite_db_path)

def postgres_connect():
    """Connect to the PostgreSQL database"""
    conn = None
    try:
        conn = psycopg2.connect(POSTGRES_URL)
    except psycopg2.OperationalError as e:
        print(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)
    return conn

def adapt_value(value):
    """Adapt SQLite value for PostgreSQL insertion"""
    if value is None:
        return None
    elif isinstance(value, (int, float)):
        return value
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, bool):
        return value
    elif isinstance(value, bytes):
        return psycopg2.Binary(value)
    elif isinstance(value, str):
        # Try to see if it's a JSON string
        try:
            json.loads(value)
            return value  # It's valid JSON
        except (ValueError, TypeError):
            pass
        
        # Try to see if it's a UUID
        try:
            uuid_obj = uuid.UUID(value)
            return str(uuid_obj)
        except (ValueError, AttributeError):
            pass
            
        return value
    else:
        return str(value)

def get_table_columns(cursor, table_name):
    """Get column names for a table"""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [info[1] for info in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting columns for {table_name}: {e}")
        return []

def get_pg_table_columns(cursor, table_name):
    """Get column names for a PostgreSQL table"""
    try:
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
        """)
        return [col[0] for col in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting PostgreSQL columns for {table_name}: {e}")
        return []

def copy_table_data(sqlite_conn, pg_conn, table_name):
    """Copy data from SQLite table to PostgreSQL table"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get table columns from both databases
    sqlite_columns = get_table_columns(sqlite_cursor, table_name)
    pg_columns = get_pg_table_columns(pg_cursor, table_name)
    
    if not sqlite_columns:
        print(f"No columns found for SQLite table {table_name}")
        return 0
        
    if not pg_columns:
        print(f"No columns found for PostgreSQL table {table_name}")
        return 0
    
    # Find common columns that exist in both databases
    common_columns = [col for col in sqlite_columns if col.lower() in [c.lower() for c in pg_columns]]
    
    if not common_columns:
        print(f"No common columns found for table {table_name}")
        return 0
        
    print(f"Found {len(common_columns)} common columns for {table_name}")
    
    column_list = ', '.join(common_columns)
    placeholders = ', '.join(['%s'] * len(common_columns))
    
    # Get data from SQLite
    try:
        sqlite_cursor.execute(f"SELECT {column_list} FROM {table_name}")
        rows = sqlite_cursor.fetchall()
    except Exception as e:
        print(f"Error fetching data from SQLite for {table_name}: {e}")
        return 0
    
    if not rows:
        print(f"No data in table {table_name}")
        return 0
    
    # Clear table in PostgreSQL
    try:
        pg_cursor.execute(f"TRUNCATE {table_name} CASCADE")
    except Exception as e:
        print(f"Error truncating PostgreSQL table {table_name}: {e}")
        print("Will try to continue with the migration without truncating...")
    
    # Insert data into PostgreSQL
    insert_count = 0
    success_count = 0
    
    for row in rows:
        adapted_row = [adapt_value(value) for value in row]
        try:
            pg_cursor.execute(
                f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})",
                adapted_row
            )
            success_count += 1
        except Exception as e:
            print(f"Error inserting row {insert_count} into {table_name}: {e}")
            # Continue with other rows instead of stopping
        
        insert_count += 1
        
        # Commit every 100 rows to avoid transaction size issues
        if success_count % 100 == 0:
            pg_conn.commit()
    
    pg_conn.commit()
    print(f"Successfully inserted {success_count} of {insert_count} rows")
    return success_count

def disable_constraints(pg_conn):
    """Disable foreign key constraints in PostgreSQL"""
    cursor = pg_conn.cursor()
    try:
        cursor.execute("ALTER TABLE users_student DROP CONSTRAINT IF EXISTS users_student_user_id_key CASCADE;")
        cursor.execute("ALTER TABLE users_admin DROP CONSTRAINT IF EXISTS users_admin_user_id_key CASCADE;")
        cursor.execute("ALTER TABLE recognition_recognitionlog DROP CONSTRAINT IF EXISTS recognition_recognitionlog_student_id_fkey CASCADE;")
        cursor.execute("ALTER TABLE users_user_groups DROP CONSTRAINT IF EXISTS users_user_groups_user_id_fkey CASCADE;")
        cursor.execute("ALTER TABLE users_user_groups DROP CONSTRAINT IF EXISTS users_user_groups_group_id_fkey CASCADE;")
        cursor.execute("ALTER TABLE users_user_user_permissions DROP CONSTRAINT IF EXISTS users_user_user_permissions_user_id_fkey CASCADE;")
        cursor.execute("ALTER TABLE users_user_user_permissions DROP CONSTRAINT IF EXISTS users_user_user_permissions_permission_id_fkey CASCADE;")
        cursor.execute("ALTER TABLE auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_group_id_fkey CASCADE;")
        cursor.execute("ALTER TABLE auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_permission_id_fkey CASCADE;")
        cursor.execute("ALTER TABLE auth_permission DROP CONSTRAINT IF EXISTS auth_permission_content_type_id_fkey CASCADE;")
        cursor.execute("ALTER TABLE django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_user_id_fkey CASCADE;")
        cursor.execute("ALTER TABLE django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_content_type_id_fkey CASCADE;")
        pg_conn.commit()
        print("Foreign key constraints disabled")
    except Exception as e:
        print(f"Error disabling constraints: {e}")
        pg_conn.rollback()

def reset_sequences(pg_conn):
    """Reset sequences in PostgreSQL after data import"""
    cursor = pg_conn.cursor()
    try:
        # Get all sequences
        cursor.execute("""
            SELECT sequence_name FROM information_schema.sequences
            WHERE sequence_schema = 'public'
        """)
        sequences = cursor.fetchall()
        
        for seq in sequences:
            seq_name = seq[0]
            print(f"Resetting sequence {seq_name}")
            # Find table and column for this sequence
            try:
                # This query tries to find the table and column that uses this sequence
                cursor.execute(f"""
                    SELECT 
                        table_name, column_name 
                    FROM 
                        information_schema.columns 
                    WHERE 
                        column_default LIKE '%{seq_name}%'
                """)
                result = cursor.fetchone()
                
                if result:
                    table_name, column_name = result
                    # Reset the sequence to the maximum value in the table
                    cursor.execute(f"""
                        SELECT setval(
                            '{seq_name}', 
                            COALESCE((SELECT MAX({column_name}) FROM {table_name}), 1), 
                            false
                        )
                    """)
                    print(f"  Reset {seq_name} for {table_name}.{column_name}")
            except Exception as e:
                print(f"  Error resetting sequence {seq_name}: {e}")
        
        pg_conn.commit()
        print("All sequences reset")
    except Exception as e:
        print(f"Error resetting sequences: {e}")
        pg_conn.rollback()

def verify_sqlite_tables(sqlite_conn):
    """Verify that tables exist in the SQLite database"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    
    if not tables:
        print("No tables found in SQLite database. This may be an empty or invalid database.")
        return False
    
    print("Found the following tables in SQLite database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    return True

def verify_postgres_tables(pg_conn):
    """Verify tables in the PostgreSQL database"""
    cursor = pg_conn.cursor()
    try:
        cursor.execute("""
            SELECT tablename FROM pg_catalog.pg_tables 
            WHERE schemaname='public';
        """)
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in PostgreSQL database. Make sure migrations have been run.")
            return False
        
        print("Found the following tables in PostgreSQL database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        return True
    except Exception as e:
        print(f"Error checking PostgreSQL tables: {e}")
        return False

def get_common_tables(sqlite_conn, pg_conn):
    """Get tables that exist in both databases"""
    # Get SQLite tables
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    sqlite_tables = [row[0] for row in sqlite_cursor.fetchall()]
    
    # Get PostgreSQL tables
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public';")
    pg_tables = [row[0] for row in pg_cursor.fetchall()]
    
    # Find common tables
    common_tables = [table for table in sqlite_tables if table in pg_tables]
    
    if not common_tables:
        print("No common tables found between SQLite and PostgreSQL.")
        return []
    
    print("Found the following common tables:")
    for table in common_tables:
        print(f"  - {table}")
    
    return common_tables

def copy_student_data(sqlite_conn, pg_conn):
    """Special handling for student data to ensure correct migration"""
    print("Using special handling for student data...")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # First, get all student data from SQLite
    try:
        sqlite_cursor.execute("SELECT * FROM users_student")
        students = sqlite_cursor.fetchall()
        
        if not students:
            print("No student data found in SQLite database")
            return 0
            
        print(f"Found {len(students)} students in SQLite database")
        
        # Get the column names
        sqlite_cursor.execute("PRAGMA table_info(users_student)")
        columns = [info[1] for info in sqlite_cursor.fetchall()]
        column_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        print(f"Student columns: {column_str}")
        
        # Get existing student data in PostgreSQL to avoid duplicates
        pg_cursor.execute("SELECT id FROM users_student")
        existing_students = set(row[0] for row in pg_cursor.fetchall())
        print(f"Found {len(existing_students)} existing students in PostgreSQL")
        
        # Get all existing users in PostgreSQL for reference
        pg_cursor.execute("SELECT id FROM users_user")
        pg_users = set(row[0] for row in pg_cursor.fetchall())
        print(f"Found {len(pg_users)} users in PostgreSQL")
        
        # Print more debug info
        print("Sample of users in PostgreSQL:")
        pg_cursor.execute("SELECT id, email FROM users_user LIMIT 5")
        for user in pg_cursor.fetchall():
            print(f"  - User ID: {user[0]}, Email: {user[1]}")
            
        # No need to truncate - we'll insert or update instead
        
        # Insert each student
        success_count = 0
        for i, student in enumerate(students):
            try:
                student_id = student[0]
                user_id = student[1]
                
                # Print debug info for this student
                print(f"Processing student {i+1}/{len(students)}: ID={student_id}, User ID={user_id}")
                
                # Skip if already exists
                if student_id in existing_students:
                    print(f"Student ID {student_id} already exists in PostgreSQL. Skipping.")
                    continue
                
                # Check if the user exists in PostgreSQL
                if user_id not in pg_users:
                    print(f"User ID {user_id} not found in PostgreSQL. Skipping student {student_id}.")
                    continue
                
                # Adapt values
                adapted_values = []
                for i, val in enumerate(student):
                    # Special handling for face_image field
                    if columns[i] == 'face_image' and val:
                        # If it's a file path rather than binary data
                        if isinstance(val, str) and os.path.exists(val):
                            with open(val, 'rb') as f:
                                adapted_values.append(psycopg2.Binary(f.read()))
                        else:
                            adapted_values.append(adapt_value(val))
                    # Special handling for date fields
                    elif columns[i] in ['created_at', 'updated_at'] and val:
                        if isinstance(val, str):
                            try:
                                dt = datetime.fromisoformat(val.replace('Z', '+00:00'))
                                adapted_values.append(dt.isoformat())
                            except ValueError:
                                adapted_values.append(val)
                        else:
                            adapted_values.append(adapt_value(val))
                    else:
                        adapted_values.append(adapt_value(val))
                
                # Insert the student with a direct INSERT statement
                pg_cursor.execute(
                    f"INSERT INTO users_student ({column_str}) VALUES ({placeholders})",
                    adapted_values
                )
                pg_conn.commit()
                success_count += 1
                print(f"Successfully migrated student ID: {student_id}")
            except Exception as e:
                print(f"Error migrating student ID {student[0]}: {e}")
                pg_conn.rollback()
                # Try simple INSERT without special handling as fallback
                try:
                    print("Attempting fallback insert...")
                    adapted_values = [adapt_value(val) for val in student]
                    pg_cursor.execute(
                        f"INSERT INTO users_student ({column_str}) VALUES ({placeholders})",
                        adapted_values
                    )
                    pg_conn.commit()
                    success_count += 1
                    print(f"Fallback migration successful for student ID: {student[0]}")
                except Exception as e2:
                    print(f"Fallback insert also failed: {e2}")
                    pg_conn.rollback()
        
        # Print final summary
        if success_count > 0:
            print(f"Successfully migrated {success_count} out of {len(students)} students")
        else:
            print("Failed to migrate any students!")
            
        return success_count
    except Exception as e:
        print(f"Error in student migration: {e}")
        pg_conn.rollback()
        return 0
        
def insert_student_directly():
    """Manually insert student records directly into PostgreSQL"""
    print("Attempting to insert students directly...")
    
    # Connect to PostgreSQL
    pg_conn = postgres_connect()
    pg_cursor = pg_conn.cursor()
    
    # Connect to SQLite
    sqlite_conn = sqlite_connect()
    sqlite_cursor = sqlite_conn.cursor()
    
    try:
        # Get student data
        sqlite_cursor.execute("SELECT * FROM users_student")
        students = sqlite_cursor.fetchall()
        
        if not students:
            print("No students found in SQLite database")
            return
            
        print(f"Found {len(students)} students in SQLite database")
        
        # Get column names
        sqlite_cursor.execute("PRAGMA table_info(users_student)")
        columns_info = sqlite_cursor.fetchall()
        columns = [info[1] for info in columns_info]
        
        # Get PostgreSQL column constraints
        pg_cursor.execute("""
            SELECT column_name, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'users_student'
            AND character_maximum_length IS NOT NULL;
        """)
        pg_constraints = {row[0]: row[1] for row in pg_cursor.fetchall()}
        print("PostgreSQL column size constraints:")
        for col, length in pg_constraints.items():
            print(f"  - {col}: {length} characters")
        
        # For each student
        for student in students:
            # Print student info
            print(f"Student ID: {student[0]}, User ID: {student[1]}")
            print(f"Name: {student[2]} {student[3]}")
            print(f"Matric Number: {student[4]}")
            
            # Ask to insert this student
            choice = input(f"Insert student {student[2]} {student[3]}? (y/n): ")
            if choice.lower() != 'y':
                continue
                
            # Adapt values with constraint checking
            adapted_values = []
            for i, val in enumerate(student):
                column_name = columns[i]
                # Check if this column has length constraints
                if column_name in pg_constraints and isinstance(val, str) and len(val) > pg_constraints[column_name]:
                    print(f"WARNING: Column '{column_name}' value '{val}' exceeds PostgreSQL limit of {pg_constraints[column_name]} characters")
                    print(f"Truncating value to: '{val[:pg_constraints[column_name]]}'")
                    val = val[:pg_constraints[column_name]]
                adapted_values.append(adapt_value(val))
                
            # Try to insert
            try:
                column_str = ', '.join(columns)
                placeholders = ', '.join(['%s'] * len(columns))
                pg_cursor.execute(
                    f"INSERT INTO users_student ({column_str}) VALUES ({placeholders})",
                    adapted_values
                )
                pg_conn.commit()
                print(f"Successfully inserted student {student[2]} {student[3]}")
            except Exception as e:
                print(f"Error inserting student: {e}")
                # Print detailed info about the values being inserted
                print("Detailed column values:")
                for i, val in enumerate(student):
                    print(f"  - {columns[i]}: '{val}' (type: {type(val).__name__}, length: {len(str(val)) if val else 0})")
                pg_conn.rollback()
                
                # Try again with interactive fixes
                print("Would you like to retry with manual value adjustments? (y/n)")
                retry = input().lower()
                if retry == 'y':
                    manual_values = []
                    for i, val in enumerate(student):
                        column_name = columns[i]
                        print(f"Current value for '{column_name}': '{val}'")
                        new_val = input(f"Enter new value (or press Enter to keep current): ")
                        if new_val:
                            manual_values.append(adapt_value(new_val))
                        else:
                            manual_values.append(adapt_value(val))
                    
                    try:
                        pg_cursor.execute(
                            f"INSERT INTO users_student ({column_str}) VALUES ({placeholders})",
                            manual_values
                        )
                        pg_conn.commit()
                        print(f"Successfully inserted student with manual values")
                    except Exception as e2:
                        print(f"Manual insert also failed: {e2}")
                        pg_conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sqlite_conn.close()
        pg_conn.close()

# Add a new function to fix the PostgreSQL schema to match SQLite
def fix_postgresql_schema():
    """Alter PostgreSQL schema to match SQLite column sizes"""
    print("Modifying PostgreSQL schema to match SQLite column sizes...")
    
    # Connect to databases
    sqlite_conn = sqlite_connect()
    sqlite_cursor = sqlite_conn.cursor()
    
    pg_conn = postgres_connect()
    pg_cursor = pg_conn.cursor()
    
    try:
        # Get SQLite student table columns and types
        sqlite_cursor.execute("PRAGMA table_info(users_student)")
        sqlite_columns = {info[1]: info[2] for info in sqlite_cursor.fetchall()}
        
        # Get PostgreSQL student table columns and constraints
        pg_cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'users_student';
        """)
        pg_columns = {row[0]: (row[1], row[2]) for row in pg_cursor.fetchall()}
        
        print("Comparing schemas...")
        for col_name, sqlite_type in sqlite_columns.items():
            if col_name in pg_columns:
                pg_type, pg_length = pg_columns[col_name]
                
                # Check if text field with potential size issues
                if 'char' in sqlite_type.lower() and pg_length is not None:
                    print(f"Column '{col_name}': SQLite={sqlite_type}, PostgreSQL={pg_type}({pg_length})")
                    
                    # Suggest to expand the column size
                    if pg_length < 255:  # Common reasonable limit
                        print(f"  Expanding '{col_name}' from {pg_length} to 255 characters")
                        try:
                            pg_cursor.execute(f"ALTER TABLE users_student ALTER COLUMN {col_name} TYPE varchar(255)")
                            pg_conn.commit()
                            print(f"  Successfully altered column '{col_name}'")
                        except Exception as e:
                            print(f"  Error altering column: {e}")
                            pg_conn.rollback()
        
        print("PostgreSQL schema update complete")
    except Exception as e:
        print(f"Error updating schema: {e}")
    finally:
        sqlite_conn.close()
        pg_conn.close()

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    print(f"Migrating data from {sqlite_db_path} to PostgreSQL...")
    
    # Connect to databases
    sqlite_conn = sqlite_connect()
    
    # Verify tables in SQLite
    if not verify_sqlite_tables(sqlite_conn):
        print("Migration aborted - no tables found in SQLite database.")
        sqlite_conn.close()
        return
    
    pg_conn = postgres_connect()
    
    # Verify tables in PostgreSQL
    if not verify_postgres_tables(pg_conn):
        print("Migration aborted - no tables found in PostgreSQL database.")
        sqlite_conn.close()
        pg_conn.close()
        return
    
    # Get common tables
    common_tables = get_common_tables(sqlite_conn, pg_conn)
    if not common_tables:
        print("Migration aborted - no common tables found.")
        sqlite_conn.close()
        pg_conn.close()
        return
    
    try:
        # Try to disable foreign key constraints - this is more targeted than session_replication_role
        print("Attempting to disable constraints...")
        disable_constraints(pg_conn)
    except Exception as e:
        print(f"Could not disable constraints: {e}")
        print("Will attempt migration anyway...")
    
    total_count = 0
    
    # Use the discovered common tables in an appropriate order
    # Start with base tables first - put users_user first, then content types, then other tables
    ordered_tables = []
    # This precise order helps with foreign key relationships
    base_tables = [
        'django_content_type',  # First due to permissions dependency
        'auth_permission', 
        'auth_group',
        'users_user',           # Users must come before student profiles
    ]

    # Add student and admin profiles next
    profile_tables = [
        'users_student',
        'users_admin',
    ]

    # Add remaining tables - order matters for foreign key references
    remaining_core_tables = [
        'auth_group_permissions',
        'users_user_groups',
        'users_user_user_permissions',
        'recognition_recognitionlog',
        'django_admin_log',
        'django_session'
    ]

    # Build the ordered list based on what's available
    for table in base_tables:
        if table in common_tables:
            ordered_tables.append(table)

    for table in profile_tables:
        if table in common_tables:
            ordered_tables.append(table)

    for table in remaining_core_tables:
        if table in common_tables:
            ordered_tables.append(table)

    # Add any other tables not explicitly listed
    for table in common_tables:
        if table not in ordered_tables:
            ordered_tables.append(table)
    
    print("\nWill migrate the following tables in this order:")
    for i, table in enumerate(ordered_tables, 1):
        print(f"{i}. {table}")
    
    # Confirm before proceeding
    proceed = input("\nProceed with migration? (yes/no): ")
    if proceed.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        sqlite_conn.close()
        pg_conn.close()
        return
    
    # Migrate base tables
    for table_name in [t for t in ordered_tables if t in base_tables]:
        try:
            print(f"Migrating table {table_name}...")
            count = copy_table_data(sqlite_conn, pg_conn, table_name)
            print(f"Migrated {count} rows from {table_name}")
            total_count += count
        except Exception as e:
            print(f"Error migrating table {table_name}: {e}")
    
    # Special handling for student data
    if 'users_student' in common_tables:
        print("\nSpecial handling for student data...")
        student_count = copy_student_data(sqlite_conn, pg_conn)
        print(f"Migrated {student_count} students with special handling")
        total_count += student_count
        # Remove from ordered tables since we've handled it specially
        if 'users_student' in ordered_tables:
            ordered_tables.remove('users_student')
    
    # Migrate remaining tables
    for table_name in [t for t in ordered_tables if t not in base_tables]:
        try:
            print(f"Migrating table {table_name}...")
            count = copy_table_data(sqlite_conn, pg_conn, table_name)
            print(f"Migrated {count} rows from {table_name}")
            total_count += count
        except Exception as e:
            print(f"Error migrating table {table_name}: {e}")
    
    # Reset sequences after data migration
    try:
        print("\nResetting sequences...")
        reset_sequences(pg_conn)
    except Exception as e:
        print(f"Error resetting sequences: {e}")
    
    # Close connections
    sqlite_conn.close()
    pg_conn.close()
    
    print(f"Migration complete. Total rows migrated: {total_count}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--direct-student-insert":
            insert_student_directly()
        elif sys.argv[1] == "--fix-schema":
            fix_postgresql_schema()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Available options:")
            print("  --direct-student-insert  : Directly insert students with interactive prompts")
            print("  --fix-schema             : Modify PostgreSQL schema to match SQLite")
    else:
        migrate_data()
