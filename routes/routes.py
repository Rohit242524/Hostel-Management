from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3

def setup_routes(app):
    app.secret_key = 'secret'
    app.permanent_session_lifetime = 3600

    def get_db():
        conn = sqlite3.connect('hostel.db')
        conn.row_factory = sqlite3.Row
        return conn

    @app.route('/')
    def home():
        return render_template('login.html')

    @app.route('/login', methods=['POST'])
    def login():
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
                    return redirect('/')
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
        with get_db() as conn:
            students = conn.execute('SELECT id, COALESCE(student_id, "Not Set") AS student_id, username, name, email FROM students').fetchall()
        return render_template('dashboard_admin.html', students=students)

    @app.route('/dashboard/student', methods=['GET','POST'])
    def student_dashboard():
        return render_template('dashboard_student.html')

    @app.route('/view_students')
    def view_students():
        with get_db() as conn:
            students = conn.execute('SELECT id, COALESCE(student_id, "Not Set") AS student_id, username, name, email FROM students').fetchall()
        return render_template('view_students.html', students=students)

    @app.route('/manage_rooms', methods=['GET', 'POST'])
    def manage_rooms():
        with get_db() as conn:
            if request.method == 'POST':
                room_number = request.form.get('room_number')
                status = request.form.get('status', 'available')

                if not room_number:
                    return jsonify({'success': False, 'message': 'Room number is required.'})

                try:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO rooms (room_number, status, current_occupancy) VALUES (?, ?, ?)',
                                (room_number, status, 0))
                    new_room_id = cursor.lastrowid
                    cursor.execute("""
                        UPDATE rooms 
                        SET max_capacity = CASE 
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

            rooms = conn.execute('SELECT id, room_number, status, max_capacity, current_occupancy FROM rooms').fetchall()
        return render_template('manage_rooms.html', rooms=rooms)

    @app.route('/view_bookings')
    def view_bookings():
        with get_db() as conn:
            pending_bookings = conn.execute('''
                SELECT b.id, b.student_id, s.student_id AS roll_number, s.name, r.room_number, b.status, b.booking_date
                FROM bookings b
                JOIN students s ON b.student_id = s.id
                JOIN rooms r ON b.room_id = r.id
                WHERE b.status = 'pending'
                ORDER BY b.booking_date ASC
            ''').fetchall()

            approved_bookings = conn.execute('''
                SELECT b.id, b.student_id, s.student_id AS roll_number, s.name, r.room_number, b.status, b.booking_date
                FROM bookings b
                JOIN students s ON b.student_id = s.id
                JOIN rooms r ON b.room_id = r.id
                WHERE b.status = 'approved'
                ORDER BY b.booking_date ASC
            ''').fetchall()

        return render_template('view_bookings.html', pending_bookings=pending_bookings, approved_bookings=approved_bookings)
    
    
    @app.route('/handle_complaints', methods=['GET'])
    def handle_complaints():
        with get_db() as conn:
            complaints = conn.execute('''
                SELECT c.id, c.student_id, s.student_id AS roll_number, s.name, c.complaint_text, c.status, c.created_at
                FROM complaints c
                JOIN students s ON c.student_id = s.id
                ORDER BY c.created_at DESC
            ''').fetchall()
        return render_template('handle_complaints.html', complaints=complaints)

    @app.route('/resolve_complaint/<int:complaint_id>', methods=['POST'])
    def resolve_complaint(complaint_id):
        with get_db() as conn:
            conn.execute("UPDATE complaints SET status = 'resolved' WHERE id = ?", (complaint_id,))
            conn.commit()
            flash('Complaint marked as resolved.', 'success')
        return redirect(url_for('handle_complaints'))

    @app.route('/my_allocation')
    def my_allocation():
        if 'user' not in session:
            flash('Please log in to view your allocation.', 'error')
            return redirect(url_for('home'))

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

    @app.route('/submit_complaint', methods=['GET', 'POST'])
    def submit_complaint():
        if 'user' not in session:
            flash('Please log in to submit a complaint.', 'error')
            return redirect(url_for('home'))

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
                    try:
                        conn.execute('INSERT INTO complaints (student_id, complaint_text, status, created_at) VALUES (?, ?, ?, ?)',
                                    (student_id, complaint_text, 'pending', '2025-05-27 03:03:00'))
                        conn.commit()
                        flash('Complaint submitted successfully.', 'success')
                    except sqlite3.Error as e:
                        flash('Failed to submit complaint: ' + str(e), 'error')

        return render_template('submit_complaint.html')

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        return redirect(url_for('home'))

    @app.route('/student_section/check_booking', methods=['GET'])
    def check_booking():
        if 'user' not in session:
            return jsonify({'already_requested': False, 'rejected': False})

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
        
    @app.route('/student_section/get_rooms', methods=['GET'])
    def get_rooms():
        with get_db() as conn:
            rooms = conn.execute("""
                SELECT id, room_number, max_capacity, current_occupancy, 
                       (max_capacity - current_occupancy) AS available_beds
                FROM rooms 
                WHERE current_occupancy < max_capacity AND status = 'available'
                ORDER BY max_capacity ASC
            """).fetchall()
        return jsonify([dict(room) for room in rooms])

    from datetime import datetime

    @app.route('/student_section/book_room', methods=['GET', 'POST'])
    def book_room():
        if 'user' not in session:
            return jsonify({'success': False, 'message': 'Please log in to book a room.'})

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

                try:
                    room_id = int(room_id)
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    conn.execute('INSERT INTO bookings (student_id, room_id, status, booking_date) VALUES (?, ?, ?, ?)',
                                (student_id, room_id, 'pending', current_time))
                    conn.commit()
                    return jsonify({'success': True, 'message': 'Room booking requested! Waiting for admin approval.'})
                except (ValueError, sqlite3.IntegrityError):
                    return jsonify({'success': False, 'message': 'Invalid room selection.'})

            return redirect(url_for('student_dashboard'))
        
    
    @app.route('/process_bookings', methods=['POST'])
    def process_bookings():
        strategy = request.form.get('strategy', 'fcfs')
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
                        (r.max_capacity - r.current_occupancy) AS remaining_capacity
                    FROM bookings b
                    JOIN rooms r ON b.room_id = r.id
                    WHERE b.status = 'pending'
                    ORDER BY (r.max_capacity - r.current_occupancy) ASC, b.booking_date ASC
                """).fetchall()
                print("SJF Bookings Order:", [(b['id'], b['room_id'], b['remaining_capacity'], b['booking_date']) for b in bookings])
            else:
                bookings = conn.execute("""
                    SELECT b.id, b.student_id, b.room_id, b.status, b.booking_date, r.max_capacity
                    FROM bookings b
                    JOIN rooms r ON b.room_id = r.id
                    WHERE b.status = 'pending'
                    ORDER BY r.max_capacity ASC, b.booking_date ASC
                """).fetchall()
                print("Priority Bookings Order:", [(b['id'], b['room_id'], b['max_capacity'], b['booking_date']) for b in bookings])

            processed_bookings = []
            for booking in bookings:
                booking_id = booking['id']
                room_id = booking['room_id']
                student_id = booking['student_id']

                room = conn.execute("""
                    SELECT max_capacity, current_occupancy 
                    FROM rooms 
                    WHERE id = ?
                """, (room_id,)).fetchone()

                if not room or room['current_occupancy'] >= room['max_capacity']:
                    conn.execute("UPDATE bookings SET status = 'rejected' WHERE id = ?", (booking_id,))
                    conn.commit()
                    print(f"Rejected booking {booking_id}: Room {room_id} is full (current_occupancy={room['current_occupancy']}, max_capacity={room['max_capacity']})")
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
                        WHEN current_occupancy + 1 >= max_capacity THEN 'occupied'
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