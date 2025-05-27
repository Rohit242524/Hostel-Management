import random
import sqlite3
from datetime import datetime, timedelta

# Connect to the database
conn = sqlite3.connect("hostel.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Drop existing tables if they exist
cursor.execute("DROP TABLE IF EXISTS admins")
cursor.execute("DROP TABLE IF EXISTS students")
cursor.execute("DROP TABLE IF EXISTS rooms")
cursor.execute("DROP TABLE IF EXISTS bookings")
cursor.execute("DROP TABLE IF EXISTS complaints")

# Create tables
cursor.execute(
    """
    CREATE TABLE admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
"""
)

cursor.execute(
    """
    CREATE TABLE students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL UNIQUE,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL
    )
"""
)

cursor.execute(
    """
    CREATE TABLE rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL,
        max_capacity INTEGER NOT NULL,
        current_occupancy INTEGER NOT NULL
    )
"""
)

cursor.execute(
    """
    CREATE TABLE bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        booking_date TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (room_id) REFERENCES rooms(id)
    )
"""
)

cursor.execute(
    """
    CREATE TABLE complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        complaint_text TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
"""
)

# Insert test data
# Admins
cursor.execute(
    "INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", "admin123")
)

# Students
students = [
    ("S001", "student1", "pass1", "Amit Sharma", "amit@example.com"),
    ("S002", "student2", "pass2", "Riya Patel", "riya@example.com"),
    ("S003", "student3", "pass3", "Vikram Singh", "vikram@example.com"),
    ("S004", "student4", "pass4", "Sneha Gupta", "sneha@example.com"),
    ("S005", "student5", "pass5", "Rahul Kumar", "rahul@example.com"),
    ("S006", "student6", "pass6", "Pooja Desai", "pooja@example.com"),
    ("S007", "student7", "pass7", "Arjun Mehta", "arjun@example.com"),
    ("S008", "student8", "pass8", "Kavya Reddy", "kavya@example.com"),
]
cursor.executemany(
    "INSERT INTO students (student_id, username, password, name, email) VALUES (?, ?, ?, ?, ?)",
    students,
)

# Rooms
for i in range(1, 13):  # 12 rooms
    room_number = f"R{i:03d}"
    max_capacity = 1 if i < 10 else (2 if i <= 25 else 3)
    cursor.execute(
        "INSERT INTO rooms (room_number, status, max_capacity, current_occupancy) VALUES (?, ?, ?, ?)",
        (room_number, "available", max_capacity, 0),
    )

# Bookings
base_time = datetime(2025, 5, 27, 4, 57, 33)
for i in range(6):  # 6 bookings
    student_id = i + 1
    room_id = random.randint(1, 12)
    booking_time = (base_time + timedelta(seconds=i * 45)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO bookings (student_id, room_id, status, booking_date) VALUES (?, ?, ?, ?)",
        (student_id, room_id, "pending", booking_time),
    )

# Complaints
complaints = [
    (1, "No hot water in the bathroom.", "pending", "2025-05-27 05:30:00"),
    (2, "Room is not cleaned properly.", "pending", "2025-05-27 05:32:00"),
]
cursor.executemany(
    "INSERT INTO complaints (student_id, complaint_text, status, created_at) VALUES (?, ?, ?, ?)",
    complaints,
)

# Commit and close
conn.commit()
conn.close()

print("Database setup complete with test data.")
