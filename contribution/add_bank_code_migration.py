#!/usr/bin/env python3
"""
Database migration script to add the missing bank_code column to bank_account table
"""

import sqlite3
import os

def add_bank_code_column():
    """Add the bank_code column to the bank_account table"""
    
    db_path = 'instance/money_saver.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if bank_code column already exists
        cursor.execute("PRAGMA table_info(bank_account)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'bank_code' in columns:
            print("bank_code column already exists in bank_account table")
            return
        
        # Add the bank_code column
        cursor.execute("""
            ALTER TABLE bank_account 
            ADD COLUMN bank_code VARCHAR(10)
        """)
        
        print("Successfully added bank_code column to bank_account table")
        
        # Commit the changes
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"Error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_bank_code_column()
