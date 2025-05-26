import sqlite3

conn = sqlite3.connect('hostel.db')
c = conn.cursor()

# Create rooms table
c.execute('''
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT UNIQUE NOT NULL,
    capacity INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'available'
)
''')

# Create bookings table
c.execute('''
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    booking_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id)
)
''')

# Insert 50 rooms if not already present
for i in range(1, 51):
    room_num = f"Room-{i:03d}"
    c.execute('SELECT id FROM rooms WHERE room_number = ?', (room_num,))
    if not c.fetchone():
        c.execute('INSERT INTO rooms (room_number, capacity, status) VALUES (?, ?, ?)',
                  (room_num, 1, 'available'))

conn.commit()
conn.close()
