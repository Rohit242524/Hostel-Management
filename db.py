import sqlite3

# Connect to the database
conn = sqlite3.connect('hostel.db')
cursor = conn.cursor()

# Create the complaints table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            complaint_text TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)
    conn.commit()
    print("Complaints table created successfully.")
except sqlite3.Error as e:
    print(f"Error creating complaints table: {e}")
finally:
    conn.close()