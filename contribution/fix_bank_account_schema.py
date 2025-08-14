#!/usr/bin/env python3
"""
Direct database fix for missing bank_code column in bank_account table
This script will either add the column or recreate the table with the correct schema
"""

import sqlite3
import os
import shutil
from datetime import datetime

def fix_bank_account_table():
    """Fix the bank_account table schema"""
    
    db_path = 'instance/money_saver.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    # Create backup
    backup_path = f'instance/money_saver_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current table structure
        cursor.execute("PRAGMA table_info(bank_account)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Current columns in bank_account: {columns}")
        
        if 'bank_code' not in columns:
            print("Adding bank_code column...")
            cursor.execute("""
                ALTER TABLE bank_account 
                ADD COLUMN bank_code VARCHAR(10)
            """)
            print("bank_code column added successfully!")
        else:
            print("bank_code column already exists")
        
        conn.commit()
        print("Database schema updated successfully!")
        
    except sqlite3.OperationalError as e:
        print(f"Error adding column: {e}")
        print("Attempting to recreate table with correct schema...")
        
        # Get existing data
        cursor.execute("SELECT * FROM bank_account")
        existing_data = cursor.fetchall()
        
        # Get table info
        cursor.execute("PRAGMA table_info(bank_account)")
        table_info = cursor.fetchall()
        
        # Drop and recreate table with correct schema
        cursor.execute("DROP TABLE IF EXISTS bank_account_new")
        cursor.execute("""
            CREATE TABLE bank_account_new (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                bank_name VARCHAR(100) NOT NULL,
                account_number VARCHAR(20) NOT NULL,
                account_name VARCHAR(100) NOT NULL,
                bvn VARCHAR(11),
                bank_code VARCHAR(10),
                recipient_code VARCHAR(100),
                is_verified BOOLEAN DEFAULT 0,
                is_default BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        """)
        
        # Copy existing data
        if existing_data:
            # Prepare insert statement based on existing columns
            placeholders = ', '.join(['?' for _ in range(len(table_info))])
            column_names = ', '.join([col[1] for col in table_info])
            
            insert_sql = f"INSERT INTO bank_account_new ({column_names}) VALUES ({placeholders})"
            cursor.executemany(insert_sql, existing_data)
        
        # Replace old table
        cursor.execute("DROP TABLE IF EXISTS bank_account")
        cursor.execute("ALTER TABLE bank_account_new RENAME TO bank_account")
        
        conn.commit()
        print("Table recreated with correct schema!")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_bank_account_table()
