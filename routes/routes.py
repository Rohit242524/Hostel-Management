from flask import render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime

def setup_routes(app):
    def get_db():
        conn = sqlite3.connect('hostel.db')
        conn.row_factory = sqlite3.Row
        return conn

    @app.route('/')
    def home():
        return render_template('login.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user_type = request.form['user_type']
            username = request.form['username']
            password = request.form['password']
            with get_db() as conn:
                if user_type == 'admin':
                    cur = conn.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password))
                else:
                    cur = conn.execute('SELECT * FROM students WHERE username = ? AND password = ?', (username, password))
                user = cur.fetchone()
            if user:
                session['user'] = username
                session['user_type'] = user_type
                return redirect(url_for('admin_dashboard' if user_type == 'admin' else 'student_dashboard'))
            flash('Invalid credentials', 'error')
        return render_template('login.html')

    @app.route('/register/student', methods=['GET', 'POST'])
    def register_student():
        if request.method == 'POST':
            student_id = request.form['student_id']
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            email = request.form['email']
            with get_db() as conn:
                try:
                    conn.execute('INSERT INTO students (student_id, username, password, name, email) VALUES (?, ?, ?, ?, ?)',
                                 (student_id, username, password, name, email))
                    conn.commit()
                    flash('Registration successful! Please log in.', 'success')
                    return redirect(url_for('login'))
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed: students.student_id" in str(e):
                        return render_template('register_student.html', error="Student ID (Roll Number) already exists")
                    elif "UNIQUE constraint failed: students.username" in str(e):
                        return render_template('register_student.html', error="Username already exists")
                    else:
                        return render_template('register_student.html', error="Registration failed")
        return render_template('register_student.html')

    @app.route('/dashboard/admin')
    def admin_dashboard():
        if 'user' not in session or session['user_type'] != 'admin':
            flash('Please log in as an admin to access this page.', 'error')
            return redirect(url_for('login'))
        
        with get_db() as conn:
            students = conn.execute('SELECT id, COALESCE(student_id, "Not Set") AS student_id, username, name, email FROM students').fetchall()
        return render_template('dashboard_admin.html', students=students)

    @app.route('/dashboard/student', methods=['GET', 'POST'])
    def student_dashboard():
        if 'user' not in session or session['user_type'] != 'student':
            flash('Please log in as a student to access this page.', 'error')
            return redirect(url_for('login'))
        return render_template('dashboard_student.html')

    @app.route('/view_students')
    def view_students():
        if 'user' not in session or session['user_type'] != 'admin':
            flash('Please log in as an admin to access this page.', 'error')
            return redirect(url_for('login'))
        
        with get_db() as conn:
            students = conn.execute('SELECT id, COALESCE(student_id, "Not Set") AS student_id, username, name, email FROM students').fetchall()
        return render_template('view_students.html', students=students)

    @app.route('/manage_rooms', methods=['GET', 'POST'])
    def manage_rooms():
        if 'user' not in session or session['user_type'] != 'admin':
            flash('Please log in as an admin to access this page.', 'error')
            return redirect(url_for('login'))
        
        with get_db() as conn:
            if request.method == 'POST':
                room_number = request.form.get('room_number')
                status = request.form.get('status', 'available')

                if not room_number:
                    return jsonify({'success': False, 'message': 'Room number is required.'})

                try:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO rooms (room_number, status, current_occupancy, capacity) VALUES (?, ?, ?, ?)',
                                   (room_number, status, 0, 1))
                    new_room_id = cursor.lastrowid
                    cursor.execute("""
                        UPDATE rooms 
                        SET capacity = CASE 
                            WHEN id < 10 THEN 1
                            WHEN id BETWEEN 10 AND 25 THEN 2
                            ELSE 3
                        END
                        WHERE id = ?
                    """, (new_room_id,))
                    conn.commit()
                    return jsonify({'success': True, 'message': 'Room added successfully.'})
                except sqlite3.IntegrityError:
                    return jsonify({'success': False, 'message': 'Room number already exists.'})

            rooms = conn.execute('SELECT id, room_number, status, capacity, current_occupancy FROM rooms').fetchall()
        return render_template('manage_rooms.html', rooms=rooms)

    @app.route('/view_bookings')
    def view_bookings():
        if 'user' not in session or session['user_type'] != 'admin':
            flash('Please log in as an admin to access this page.', 'error')
            return redirect(url_for('login'))
        
        try:
            with get_db() as conn:
                pending_bookings = conn.execute("""
                    SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, 
                           s.student_id AS roll_number, s.name, r.room_number
                    FROM bookings b
                    JOIN students s ON b.student_id = s.id
                    JOIN rooms r ON b.room_id = r.id
                    WHERE b.status = 'pending'
                    ORDER BY b.booking_date ASC
                """).fetchall()

                approved_bookings = conn.execute("""
                    SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, 
                           s.student_id AS roll_number, s.name, r.room_number
                    FROM bookings b
                    JOIN students s ON b.student_id = s.id
                    JOIN rooms r ON b.room_id = r.id
                    WHERE b.status = 'approved'
                    ORDER BY b.booking_date ASC
                """).fetchall()

                rejected_bookings = conn.execute("""
                    SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, 
                           s.student_id AS roll_number, s.name, r.room_number
                    FROM bookings b
                    JOIN students s ON b.student_id = s.id
                    JOIN rooms r ON b.room_id = r.id
                    WHERE b.status = 'rejected'
                    ORDER BY b.booking_date ASC
                """).fetchall()

            return render_template('view_bookings.html', 
                                  pending_bookings=pending_bookings, 
                                  approved_bookings=approved_bookings,
                                  rejected_bookings=rejected_bookings)
        except sqlite3.Error as e:
            print(f"Database error in view_bookings: {e}")
            flash('Database error occurred.', 'error')
            return redirect(url_for('admin_dashboard'))

    @app.route('/handle_complaints', methods=['GET'])
    def handle_complaints():
        if 'user' not in session or session['user_type'] != 'admin':
            flash('Please log in as an admin to access this page.', 'error')
            return redirect(url_for('login'))
        
        try:
            with get_db() as conn:
                complaints = conn.execute('''
                    SELECT c.id, c.student_id, s.student_id AS roll_number, s.name, c.complaint_text, c.status, c.created_at
                    FROM complaints c
                    JOIN students s ON c.student_id = s.id
                    ORDER BY c.created_at DESC
                ''').fetchall()
            return render_template('handle_complaints.html', complaints=complaints)
        except sqlite3.Error as e:
            print(f"Database error in handle_complaints: {e}")
            flash('Database error occurred.', 'error')
            return redirect(url_for('admin_dashboard'))

    @app.route('/resolve_complaint/<int:complaint_id>', methods=['POST'])
    def resolve_complaint(complaint_id):
        if 'user' not in session or session['user_type'] != 'admin':
            flash('Please log in as an admin to access this page.', 'error')
            return redirect(url_for('login'))
        
        try:
            with get_db() as conn:
                conn.execute("UPDATE complaints SET status = 'resolved' WHERE id = ?", (complaint_id,))
                conn.commit()
                flash('Complaint marked as resolved.', 'success')
            return redirect(url_for('handle_complaints'))
        except sqlite3.Error as e:
            print(f"Database error in resolve_complaint: {e}")
            flash('Database error occurred.', 'error')
            return redirect(url_for('handle_complaints'))

    @app.route('/my_allocation')
    def my_allocation():
        if 'user' not in session or session['user_type'] != 'student':
            flash('Please log in to view your allocation.', 'error')
            return redirect(url_for('login'))

        try:
            with get_db() as conn:
                username = session['user']
                student = conn.execute('SELECT id FROM students WHERE username = ?', (username,)).fetchone()

                if not student:
                    flash('Student not found.', 'error')
                    return redirect(url_for('student_dashboard'))

                student_id = student['id']
                allocation = conn.execute('''
                    SELECT r.room_number, b.status, b.booking_date
                    FROM bookings b
                    JOIN rooms r ON b.room_id = r.id
                    WHERE b.student_id = ? AND b.status = 'approved'
                ''', (student_id,)).fetchone()

            return render_template('my_allocation.html', allocation=allocation)
        except sqlite3.Error as e:
            print(f"Database error in my_allocation: {e}")
            flash('Database error occurred.', 'error')
            return redirect(url_for('student_dashboard'))

    @app.route('/submit_complaint', methods=['GET', 'POST'])
    def submit_complaint():
        if 'user' not in session or session['user_type'] != 'student':
            flash('Please log in to submit a complaint.', 'error')
            return redirect(url_for('login'))

        try:
            with get_db() as conn:
                username = session['user']
                student = conn.execute('SELECT id FROM students WHERE username = ?', (username,)).fetchone()

                if not student:
                    flash('Student not found.', 'error')
                    return redirect(url_for('student_dashboard'))

                if request.method == 'POST':
                    complaint_text = request.form.get('complaint')
                    student_id = student['id']

                    if not complaint_text:
                        flash('Complaint cannot be empty.', 'error')
                    else:
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        conn.execute('INSERT INTO complaints (student_id, complaint_text, status, created_at) VALUES (?, ?, ?, ?)',
                                     (student_id, complaint_text, 'pending', current_time))
                        conn.commit()
                        flash('Complaint submitted successfully.', 'success')

            return render_template('submit_complaint.html')
        except sqlite3.Error as e:
            print(f"Database error in submit_complaint: {e}")
            flash('Failed to submit complaint.', 'error')
            return render_template('submit_complaint.html')

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        session.pop('user_type', None)
        flash('You have been logged out.', 'info')
        return redirect(url_for('home'))

    @app.route('/student_section/check_booking', methods=['GET'])
    def check_booking():
        if 'user' not in session or session['user_type'] != 'student':
            return jsonify({'already_requested': False, 'rejected': False})

        try:
            with get_db() as conn:
                username = session['user']
                student = conn.execute('SELECT id FROM students WHERE username = ?', (username,)).fetchone()

                if not student:
                    return jsonify({'already_requested': False, 'rejected': False})

                student_id = student['id']
                existing_booking = conn.execute(
                    "SELECT * FROM bookings WHERE student_id = ? AND status IN ('pending', 'approved')",
                    (student_id,)
                ).fetchone()
                rejected_booking = conn.execute(
                    "SELECT * FROM bookings WHERE student_id = ? AND status = 'rejected' ORDER BY booking_date DESC LIMIT 1",
                    (student_id,)
                ).fetchone()

                return jsonify({
                    'already_requested': existing_booking is not None,
                    'rejected': rejected_booking is not None
                })
        except sqlite3.Error as e:
            print(f"Database error in check_booking: {e}")
            return jsonify({'already_requested': False, 'rejected': False})

    @app.route('/student_section/get_rooms', methods=['GET'])
    def get_rooms():
        try:
            with get_db() as conn:
                rooms = conn.execute("""
                    SELECT id, room_number, capacity, current_occupancy, 
                           (capacity - current_occupancy) AS available_beds
                    FROM rooms 
                    WHERE current_occupancy < capacity AND status = 'available'
                    ORDER BY capacity ASC
                """).fetchall()
            return jsonify([dict(room) for room in rooms])
        except sqlite3.Error as e:
            print(f"Database error in get_rooms: {e}")
            return jsonify([])

    @app.route('/student_section/book_room', methods=['GET', 'POST'])
    def book_room():
        if 'user' not in session or session['user_type'] != 'student':
            return jsonify({'success': False, 'message': 'Please log in to book a room.'})

        try:
            with get_db() as conn:
                username = session['user']
                student = conn.execute('SELECT id FROM students WHERE username = ?', (username,)).fetchone()

                if not student:
                    return jsonify({'success': False, 'message': 'Student not found.'})

                student_id = student['id']
                existing_booking = conn.execute(
                    "SELECT * FROM bookings WHERE student_id = ? AND status IN ('pending', 'approved')",
                    (student_id,)
                ).fetchone()
                if existing_booking:
                    return jsonify({'success': False, 'message': 'You already have a pending or approved booking.'})

                if request.method == 'POST':
                    name = request.form.get('name')
                    email = request.form.get('email')
                    phone = request.form.get('phone')
                    room_id = request.form.get('room_id')
                    payment_method = request.form.get('payment_method')

                    if not all([name, email, phone, room_id, payment_method]):
                        return jsonify({'success': False, 'message': 'All fields are required.'})

                    room_id = int(room_id)
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    conn.execute('INSERT INTO bookings (student_id, room_id, status, booking_date) VALUES (?, ?, ?, ?)',
                                 (student_id, room_id, 'pending', current_time))
                    conn.commit()
                    return jsonify({'success': True, 'message': 'Room booking requested! Waiting for admin approval.'})

                return redirect(url_for('student_dashboard'))
        except (ValueError, sqlite3.IntegrityError) as e:
            print(f"Error in book_room: {e}")
            return jsonify({'success': False, 'message': 'Invalid room selection.'})
        except sqlite3.Error as e:
            print(f"Database error in book_room: {e}")
            return jsonify({'success': False, 'message': 'Database error occurred.'})

    @app.route('/process_bookings', methods=['POST'])
    def process_bookings():
        if 'user' not in session or session['user_type'] != 'admin':
            flash('Please log in as an admin to access this page.', 'error')
            return redirect(url_for('login'))

        strategy = request.form.get('strategy', 'fcfs')
        try:
            with get_db() as conn:
                if strategy == 'fcfs':
                    bookings = conn.execute("""
                        SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date
                        FROM bookings b
                        WHERE b.status = 'pending'
                        ORDER BY b.booking_date ASC
                    """).fetchall()
                    print("FCFS Bookings Order:", [(b['id'], b['booking_date']) for b in bookings])
                elif strategy == 'sjf':
                    bookings = conn.execute("""
                        SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, 
                               (r.capacity - r.current_occupancy) AS remaining_capacity
                        FROM bookings b
                        JOIN rooms r ON b.room_id = r.id
                        WHERE b.status = 'pending'
                        ORDER BY (r.capacity - r.current_occupancy) ASC, b.booking_date ASC
                    """).fetchall()
                    print("SJF Bookings Order:", [(b['id'], b['room_id'], b['remaining_capacity'], b['booking_date']) for b in bookings])
                else:
                    bookings = conn.execute("""
                        SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, r.capacity
                        FROM bookings b
                        JOIN rooms r ON b.room_id = r.id
                        WHERE b.status = 'pending'
                        ORDER BY r.capacity ASC, b.booking_date ASC
                    """).fetchall()
                    print("Priority Bookings Order:", [(b['id'], b['room_id'], b['capacity'], b['booking_date']) for b in bookings])

                processed_bookings = []
                for booking in bookings:
                    booking_id = booking['id']
                    room_id = booking['room_id']
                    student_id = booking['student_id']

                    room = conn.execute("""
                        SELECT capacity, current_occupancy 
                        FROM rooms 
                        WHERE id = ?
                    """, (room_id,)).fetchone()

                    if not room or room['current_occupancy'] >= room['capacity']:
                        conn.execute("UPDATE bookings SET status = 'rejected' WHERE id = ?", (booking_id,))
                        conn.commit()
                        print(f"Rejected booking {booking_id}: Room {room_id} is full (current_occupancy={room['current_occupancy'] if room else 'N/A'}, capacity={room['capacity'] if room else 'N/A'})")
                        continue

                    conn.execute("UPDATE bookings SET status = 'approved' WHERE id = ?", (booking_id,))
                    conn.execute("""
                        UPDATE rooms 
                        SET current_occupancy = current_occupancy + 1
                        WHERE id = ?
                    """, (room_id,))
                    conn.execute("""
                        UPDATE rooms 
                        SET status = CASE 
                            WHEN current_occupancy >= capacity THEN 'occupied'
                            ELSE 'available'
                        END
                        WHERE id = ?
                    """, (room_id,))
                    conn.commit()
                    processed_bookings.append((booking_id, room_id))
                    print(f"Approved booking {booking_id}: Room {room_id}")

                print("Processed Bookings Order:", processed_bookings)
                flash('Bookings processed successfully.', 'success')
            return redirect(url_for('view_bookings'))
        except sqlite3.Error as e:
            print(f"Database error in process_bookings: {e}")
            flash('Database error occurred.', 'error')
            return redirect(url_for('view_bookings'))

    @app.route('/sort_bookings', methods=['POST'])
    def sort_bookings():
        if 'user' not in session or session['user_type'] != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403

        strategy = request.form.get('strategy', 'fcfs')
        try:
            with get_db() as conn:
                if strategy == 'fcfs':
                    bookings = conn.execute("""
                        SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, 
                               s.student_id AS roll_number, s.name, r.room_number
                        FROM bookings b
                        JOIN students s ON b.student_id = s.id
                        JOIN rooms r ON b.room_id = r.id
                        WHERE b.status = 'pending'
                        ORDER BY b.booking_date ASC
                    """).fetchall()
                    print("FCFS Sort Order:", [(b['id'], b['booking_date']) for b in bookings])
                elif strategy == 'sjf':
                    bookings = conn.execute("""
                        SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, 
                               s.student_id AS roll_number, s.name, r.room_number,
                               (r.capacity - r.current_occupancy) AS remaining_capacity
                        FROM bookings b
                        JOIN students s ON b.student_id = s.id
                        JOIN rooms r ON b.room_id = r.id
                        WHERE b.status = 'pending'
                        ORDER BY (r.capacity - r.current_occupancy) ASC, b.booking_date ASC
                    """).fetchall()
                    print("SJF Sort Order:", [(b['id'], b['room_id'], b['remaining_capacity'], b['booking_date']) for b in bookings])
                else:
                    bookings = conn.execute("""
                        SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, 
                               s.student_id AS roll_number, s.name, r.room_number,
                               r.capacity
                        FROM bookings b
                        JOIN students s ON b.student_id = s.id
                        JOIN rooms r ON b.room_id = r.id
                        WHERE b.status = 'pending'
                        ORDER BY r.capacity ASC, b.booking_date ASC
                    """).fetchall()
                    print("Priority Sort Order:", [(b['id'], b['room_id'], b['capacity'], b['booking_date']) for b in bookings])

                bookings_list = [dict(booking) for booking in bookings]
                return jsonify(bookings_list)
        except sqlite3.Error as e:
            print(f"Database error in sort_bookings: {e}")
            return jsonify({'error': 'Database error'}), 500

    @app.route('/load_section', methods=['GET'])
    def load_section():
        try:
            if 'user' not in session or session['user_type'] != 'admin':
                return jsonify({'error': 'Unauthorized', 'redirect': url_for('login')}), 403
            
            section = request.args.get('section')
            with get_db() as conn:
                if section == 'students':
                    students = conn.execute('SELECT id, COALESCE(student_id, "Not Set") AS student_id, username, name, email FROM students').fetchall()
                    return render_template('view_students.html', students=students)
                elif section == 'rooms':
                    rooms = conn.execute('SELECT id, room_number, status, capacity, current_occupancy FROM rooms').fetchall()
                    return render_template('manage_rooms.html', rooms=rooms)
                elif section == 'bookings':
                    pending_bookings = conn.execute("""
                        SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, 
                               s.student_id AS roll_number, s.name, r.room_number
                        FROM bookings b
                        JOIN students s ON b.student_id = s.id
                        JOIN rooms r ON b.room_id = r.id
                        WHERE b.status = 'pending'
                        ORDER BY b.booking_date ASC
                    """).fetchall()

                    approved_bookings = conn.execute("""
                        SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, 
                               s.student_id AS roll_number, s.name, r.room_number
                        FROM bookings b
                        JOIN students s ON b.student_id = s.id
                        JOIN rooms r ON b.room_id = r.id
                        WHERE b.status = 'approved'
                        ORDER BY b.booking_date ASC
                    """).fetchall()

                    rejected_bookings = conn.execute("""
                        SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, 
                               s.student_id AS roll_number, s.name, r.room_number
                        FROM bookings b
                        JOIN students s ON b.student_id = s.id
                        JOIN rooms r ON b.room_id = r.id
                        WHERE b.status = 'rejected'
                        ORDER BY b.booking_date ASC
                    """).fetchall()

                    return render_template('view_bookings.html', 
                                          pending_bookings=pending_bookings, 
                                          approved_bookings=approved_bookings,
                                          rejected_bookings=rejected_bookings)
                elif section == 'complaints':
                    complaints = conn.execute('''
                        SELECT c.id, c.student_id, s.student_id AS roll_number, s.name, c.complaint_text, c.status, c.created_at
                        FROM complaints c
                        JOIN students s ON c.student_id = s.id
                        ORDER BY c.created_at DESC
                    ''').fetchall()
                    return render_template('handle_complaints.html', complaints=complaints)
                else:
                    return jsonify({'error': 'Invalid section'}), 404
        except sqlite3.Error as e:
            print(f"Database error in load_section: {e}")
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            print(f"Error loading section: {e}")
            return jsonify({'error': 'Server error'}), 500