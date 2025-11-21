# backend/services/create_db.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from models.base import Base, Department, Employee, Document

DB_FILE = "test.db"

# Try to remove the old DB file, with multiple attempts in case it's locked
max_attempts = 5
attempt = 0
while os.path.exists(DB_FILE) and attempt < max_attempts:
    try:
        os.remove(DB_FILE)
        print(f"Removed old database file: {DB_FILE}")
        break
    except PermissionError:
        attempt += 1
        print(f"Database file is locked. Attempt {attempt} of {max_attempts}")
        import time
        time.sleep(1)

if attempt == max_attempts:
    print("Could not remove old database file, but continuing with creation anyway")

engine = create_engine(f"sqlite:///{DB_FILE}")

# Drop all tables before recreating them
Base.metadata.drop_all(engine)

# Create all tables
Base.metadata.create_all(engine)

with engine.connect() as conn:
    # --- Step 1: Create Tables ---
    print("Creating tables...")
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS departments (
        dept_id INTEGER PRIMARY KEY,
        dept_name VARCHAR(50) NOT NULL
    )
    """))
    
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS employees (
        emp_id INTEGER PRIMARY KEY,
        full_name VARCHAR(100) NOT NULL,
        dept_id INTEGER,
        salary INTEGER,
        FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
    )
    """))

    # --- Step 2: Insert Sample Data ---
    print("Inserting sample data...")
    # Insert departments first
    conn.execute(text("INSERT INTO departments (dept_id, dept_name) VALUES (1, 'Engineering'), (2, 'Human Resources'), (3, 'Sales')"))

    # Insert employees and link them to departments via dept_id
    conn.execute(text("""
    INSERT INTO employees (emp_id, full_name, dept_id, salary) VALUES
        (101, 'Alice Johnson', 1, 90000),
        (102, 'Bob Williams', 1, 85000),
        (103, 'Charlie Brown', 3, 72000),
        (104, 'Diana Prince', 2, 78000),
        (105, 'Ethan Hunt', 1, 95000)
    """))
    
    # Commit the changes to save the data
    conn.commit()

print(f"Database '{DB_FILE}' with tables and sample data created successfully! ✅")