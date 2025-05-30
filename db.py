import sqlite3

# Connect to the database
conn = sqlite3.connect('hostel.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    # Step 1: Print the current state of the tables (for verification)
    print("Before Reset:")
    
    # Students table
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    print(f"Students table: {len(students)} rows")
    for student in students:
        print(f"Student ID: {student['id']}, Username: {student['username']}, Name: {student['name']}")

    # Bookings table
    cursor.execute("SELECT * FROM bookings")
    bookings = cursor.fetchall()
    print(f"Bookings table: {len(bookings)} rows")
    for booking in bookings:
        print(f"Booking ID: {booking['id']}, Student ID: {booking['student_id']}, Room ID: {booking['room_id']}, Status: {booking['status']}")

    # Complaints table
    cursor.execute("SELECT * FROM complaints")
    complaints = cursor.fetchall()
    print(f"Complaints table: {len(complaints)} rows")
    for complaint in complaints:
        print(f"Complaint ID: {complaint['id']}, Student ID: {complaint['student_id']}, Status: {complaint['status']}")

    # Rooms table (current_occupancy)
    cursor.execute("SELECT id, room_number, current_occupancy, status FROM rooms")
    rooms = cursor.fetchall()
    print(f"Rooms table: {len(rooms)} rows")
    for room in rooms:
        print(f"Room ID: {room['id']}, Room Number: {room['room_number']}, Current Occupancy: {room['current_occupancy']}, Status: {room['status']}")

    # Step 2: Clear the students, bookings, and complaints tables
    cursor.execute("DELETE FROM students")
    cursor.execute("DELETE FROM bookings")
    cursor.execute("DELETE FROM complaints")
    cursor.execute("DELETE FROM sqlite_sequence")
    print("\nCleared data from students, bookings, and complaints tables.")

    # Step 3: Reset current_occupancy to 0 and set status to 'available' in the rooms table
    cursor.execute("UPDATE rooms SET current_occupancy = 0, status = 'available'")
    print("Reset current_occupancy to 0 and set status to 'available' for all rooms.")

    # Step 4: Commit the changes
    conn.commit()

    # Step 5: Print the state after reset (for verification)
    print("\nAfter Reset:")
    
    # Students table
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    print(f"Students table: {len(students)} rows")

    # Bookings table
    cursor.execute("SELECT * FROM bookings")
    bookings = cursor.fetchall()
    print(f"Bookings table: {len(bookings)} rows")

    # Complaints table
    cursor.execute("SELECT * FROM complaints")
    complaints = cursor.fetchall()
    print(f"Complaints table: {len(complaints)} rows")

    # Rooms table (current_occupancy)
    cursor.execute("SELECT id, room_number, current_occupancy, status FROM rooms")
    rooms = cursor.fetchall()
    print(f"Rooms table: {len(rooms)} rows")
    for room in rooms:
        print(f"Room ID: {room['id']}, Room Number: {room['room_number']}, Current Occupancy: {room['current_occupancy']}, Status: {room['status']}")

except sqlite3.Error as e:
    print(f"Error resetting database: {e}")
finally:
    conn.close()