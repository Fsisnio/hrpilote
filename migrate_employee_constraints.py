#!/usr/bin/env python3
"""
Migration script to update employee table constraints for multi-tenancy support.
This script removes the global unique constraint on employee_id and adds a composite unique constraint.
"""

import sys
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Run the migration to update employee table constraints"""
    
    # Create database engine
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if the constraint already exists
                result = conn.execute(text("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'employees' 
                    AND constraint_type = 'UNIQUE'
                    AND constraint_name = 'uq_employee_id_organization'
                """))
                
                if result.fetchone():
                    print("✅ Composite unique constraint already exists")
                else:
                    # Drop the existing unique constraint on employee_id if it exists
                    print("🔍 Checking for existing unique constraint on employee_id...")
                    
                    # Get the constraint name for employee_id unique constraint
                    constraint_result = conn.execute(text("""
                        SELECT constraint_name 
                        FROM information_schema.table_constraints 
                        WHERE table_name = 'employees' 
                        AND constraint_type = 'UNIQUE'
                        AND constraint_name LIKE '%employee_id%'
                    """))
                    
                    constraint_row = constraint_result.fetchone()
                    if constraint_row:
                        constraint_name = constraint_row[0]
                        print(f"🗑️  Dropping existing unique constraint: {constraint_name}")
                        conn.execute(text(f"ALTER TABLE employees DROP CONSTRAINT {constraint_name}"))
                    
                    # Add the new composite unique constraint
                    print("➕ Adding composite unique constraint (employee_id, organization_id)")
                    conn.execute(text("""
                        ALTER TABLE employees 
                        ADD CONSTRAINT uq_employee_id_organization 
                        UNIQUE (employee_id, organization_id)
                    """))
                    
                    print("✅ Successfully added composite unique constraint")
                
                # Commit the transaction
                trans.commit()
                print("🎉 Migration completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

def rollback_migration():
    """Rollback the migration (remove composite constraint and restore global unique)"""
    
    # Create database engine
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Drop the composite unique constraint
                print("🗑️  Dropping composite unique constraint...")
                conn.execute(text("ALTER TABLE employees DROP CONSTRAINT uq_employee_id_organization"))
                
                # Add back the global unique constraint on employee_id
                print("➕ Adding global unique constraint on employee_id...")
                conn.execute(text("ALTER TABLE employees ADD CONSTRAINT uq_employee_id UNIQUE (employee_id)"))
                
                # Commit the transaction
                trans.commit()
                print("✅ Rollback completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Rollback failed: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print("🔄 Rolling back employee constraint migration...")
        rollback_migration()
    else:
        print("🚀 Starting employee constraint migration...")
        print("This will allow the same employee_id to exist in different organizations.")
        print("")
        
        # Ask for confirmation
        response = input("Do you want to proceed? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            run_migration()
        else:
            print("❌ Migration cancelled")
            sys.exit(0)
