"""
seed_database.py
Initializes and populates a local SQLite database for the NLP to SQL Query Assistant.
Creates multi-table relational schema: departments, employees, projects, sales_records.
"""

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "company_database.sqlite"

def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove old database if exists to ensure clean state
    if db_path.exists():
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Departments table
    cursor.execute("""
    CREATE TABLE departments (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_name TEXT NOT NULL UNIQUE,
        budget REAL NOT NULL,
        location TEXT NOT NULL,
        head_of_dept TEXT NOT NULL
    );
    """)
    
    # 2. Employees table
    cursor.execute("""
    CREATE TABLE employees (
        emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        dept_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        salary REAL NOT NULL,
        hire_date TEXT NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)
    
    # 3. Projects table
    cursor.execute("""
    CREATE TABLE projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        dept_id INTEGER NOT NULL,
        budget REAL NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        status TEXT NOT NULL CHECK(status IN ('Planning', 'In Progress', 'Completed', 'On Hold')),
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)
    
    # 4. Sales Records table
    cursor.execute("""
    CREATE TABLE sales_records (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER NOT NULL,
        client_name TEXT NOT NULL,
        deal_amount REAL NOT NULL,
        sale_date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Closed Won', 'In Negotiation', 'Lead', 'Closed Lost')),
        payment_terms TEXT NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
    );
    """)
    
    # Seed Departments
    departments_data = [
        ("Engineering", 1250000.0, "Building A - Floor 3", "Alice Chen"),
        ("Sales & Marketing", 850000.0, "Building B - Floor 1", "Marcus Vance"),
        ("Human Resources", 400000.0, "Building A - Floor 1", "Sarah Jenkins"),
        ("Product Management", 600000.0, "Building A - Floor 2", "David Kim"),
        ("Customer Success", 350000.0, "Building B - Floor 2", "Elena Rostova")
    ]
    cursor.executemany(
        "INSERT INTO departments (dept_name, budget, location, head_of_dept) VALUES (?, ?, ?, ?)",
        departments_data
    )
    
    # Seed Employees
    employees_data = [
        ("Liam", "Smith", "liam.smith@company.com", 1, "Principal Architect", 165000.0, "2021-03-15"),
        ("Sophia", "Johnson", "sophia.j@company.com", 1, "Senior Backend Engineer", 135000.0, "2022-01-10"),
        ("Noah", "Williams", "noah.w@company.com", 1, "Full Stack Engineer", 115000.0, "2023-06-01"),
        ("Ava", "Brown", "ava.brown@company.com", 1, "DevOps Engineer", 120000.0, "2022-09-18"),
        ("Ethan", "Jones", "ethan.jones@company.com", 2, "Sales Director", 150000.0, "2020-11-01"),
        ("Isabella", "Garcia", "isabella.g@company.com", 2, "Account Executive", 95000.0, "2023-02-14"),
        ("Lucas", "Miller", "lucas.m@company.com", 2, "Growth Marketing Lead", 110000.0, "2021-08-20"),
        ("Mia", "Davis", "mia.davis@company.com", 3, "HR Business Partner", 90000.0, "2021-05-12"),
        ("James", "Rodriguez", "james.r@company.com", 3, "Talent Acquisition Lead", 85000.0, "2022-04-05"),
        ("Oliver", "Martinez", "oliver.m@company.com", 4, "VP of Product", 175000.0, "2020-02-15"),
        ("Charlotte", "Hernandez", "charlotte.h@company.com", 4, "Senior Product Manager", 130000.0, "2022-07-22"),
        ("Benjamin", "Lopez", "benjamin.l@company.com", 4, "UI/UX Designer", 105000.0, "2023-01-09"),
        ("Amelia", "Gonzalez", "amelia.g@company.com", 5, "Customer Success Manager", 88000.0, "2022-10-30"),
        ("Harper", "Wilson", "harper.w@company.com", 5, "Support Specialist", 62000.0, "2023-08-11"),
        ("Alexander", "Anderson", "alexander.a@company.com", 2, "Senior Sales Manager", 125000.0, "2021-04-19")
    ]
    cursor.executemany(
        "INSERT INTO employees (first_name, last_name, email, dept_id, role, salary, hire_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        employees_data
    )
    
    # Seed Projects
    projects_data = [
        ("Cloud Modernization & Migration", 1, 350000.0, "2025-01-10", "2026-06-30", "In Progress"),
        ("Real-time AI Analytics Platform", 1, 450000.0, "2025-03-01", "2026-12-31", "In Progress"),
        ("Global Brand Refresh Campaign", 2, 180000.0, "2025-02-01", "2025-08-15", "Completed"),
        ("Lead Generation Automation", 2, 120000.0, "2025-04-01", "2026-03-01", "In Progress"),
        ("Internal HR Portal 2.0", 3, 90000.0, "2025-05-15", "2025-11-30", "Completed"),
        ("Mobile App Redesign", 4, 220000.0, "2025-06-01", "2026-05-30", "In Progress"),
        ("Customer Retention & Onboarding", 5, 80000.0, "2025-01-20", "2025-09-30", "Completed"),
        ("Enterprise Security Audit & SOC2", 1, 150000.0, "2026-01-15", "2026-07-31", "Planning")
    ]
    cursor.executemany(
        "INSERT INTO projects (project_name, dept_id, budget, start_date, end_date, status) VALUES (?, ?, ?, ?, ?, ?)",
        projects_data
    )
    
    # Seed Sales Records
    sales_data = [
        (5, "Acme Corporation", 185000.0, "2025-01-15", "Closed Won", "Net 30"),
        (6, "Globex International", 92000.0, "2025-01-28", "Closed Won", "Net 60"),
        (15, "Initech Systems", 140000.0, "2025-02-05", "Closed Won", "Net 30"),
        (6, "Umbrella Enterprises", 65000.0, "2025-02-18", "In Negotiation", "Net 45"),
        (5, "Stark Industries", 320000.0, "2025-03-02", "Closed Won", "Annual Prepaid"),
        (15, "Wayne Enterprises", 210000.0, "2025-03-12", "Closed Won", "Net 30"),
        (6, "Cyberdyne Systems", 78000.0, "2025-03-25", "Lead", "Net 30"),
        (5, "Massive Dynamic", 195000.0, "2025-04-04", "Closed Won", "Net 60"),
        (15, "Hooli Corporation", 115000.0, "2025-04-19", "In Negotiation", "Net 30"),
        (6, "Soylent Corp", 45000.0, "2025-05-02", "Closed Lost", "Net 30"),
        (5, "Pied Piper", 160000.0, "2025-05-15", "Closed Won", "Annual Prepaid"),
        (15, "Wonka Industries", 88000.0, "2025-05-29", "Closed Won", "Net 45"),
        (6, "Tyrell Corporation", 250000.0, "2025-06-10", "In Negotiation", "Net 60"),
        (5, "Gekko & Co", 130000.0, "2025-06-22", "Closed Won", "Net 30"),
        (15, "Oscorp", 175000.0, "2025-07-08", "Closed Won", "Net 30")
    ]
    cursor.executemany(
        "INSERT INTO sales_records (emp_id, client_name, deal_amount, sale_date, status, payment_terms) VALUES (?, ?, ?, ?, ?, ?)",
        sales_data
    )
    
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Database successfully initialized and seeded at: {db_path}")

if __name__ == "__main__":
    init_db()
