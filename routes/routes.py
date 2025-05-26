from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

def setup_routes(app):
    app.secret_key = 'secret'

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
        conn = get_db()

        table = 'admins' if user_type == 'admin' else 'students'
        cur = conn.execute(f'SELECT * FROM {table} WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        if user:
            session['user'] = username
            return redirect(url_for('admin_dashboard' if user_type == 'admin' else 'student_dashboard'))

        flash('Invalid credentials', 'error')
        return render_template('login.html')

    @app.route('/register/student', methods=['GET', 'POST'])
    def register_student():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            email = request.form['email']
            conn = get_db()
            try:
                conn.execute('INSERT INTO students (username, password, name, email) VALUES (?, ?, ?, ?)',
                             (username, password, name, email))
                conn.commit()
                return redirect('/')
            except sqlite3.IntegrityError:
                return render_template('register_student.html', error="Username already exists")
        return render_template('register_student.html')

    @app.route('/dashboard/admin')
    def admin_dashboard():
        conn = get_db()
        students = conn.execute('SELECT id, username, name, email FROM students').fetchall()
        return render_template('dashboard_admin.html', students=students)

    @app.route('/dashboard/student', methods=['GET','POST'])
    def student_dashboard():
        return render_template('dashboard_student.html')

    @app.route('/view_students')
    def view_students():
        conn = get_db()
        students = conn.execute('SELECT id, username, name, email FROM students').fetchall()
        return render_template('view_students.html', students=students)

    @app.route('/manage_rooms')
    def manage_rooms():
        return render_template('manage_rooms.html')

    @app.route('/view_bookings')
    def view_bookings():
        return render_template('view_bookings.html')

    @app.route('/handle_complaints')
    def handle_complaints():
        return render_template('handle_complaints.html')

    @app.route('/my_allocation')
    def my_allocation():
        return render_template('my_allocation.html')

    @app.route('/submit_complaint', methods=['GET', 'POST'])
    def submit_complaint():
        if request.method == 'POST':
            # Save complaint to DB logic here
            flash('Complaint submitted.', 'success')
        return render_template('submit_complaint.html')

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        return redirect(url_for('home'))

    @app.route('/student_section/book_room', methods=['GET', 'POST'])
    def book_room():
        if 'user' not in session:
            return redirect(url_for('home'))

        conn = get_db()
        username = session['user']
        student = conn.execute('SELECT id FROM students WHERE username = ?', (username,)).fetchone()

        if not student:
            flash('Student not found.', 'error')
            return redirect(url_for('home'))

        student_id = student['id']
        existing_booking = conn.execute("SELECT * FROM bookings WHERE student_id = ? AND status IN ('pending', 'approved')", (student_id,)).fetchone()
        already_requested = existing_booking is not None

        if request.method == 'POST' and not already_requested:
            room_id = request.form.get('room_id')
            if room_id:
                conn.execute('INSERT INTO bookings (student_id, room_id, status) VALUES (?, ?, ?)',
                             (student_id, room_id, 'pending'))
                conn.commit()
                flash('Room booking requested! Waiting for admin approval.', 'success')
                return redirect(url_for('book_room'))

        rooms = conn.execute("SELECT * FROM rooms WHERE status = 'available'").fetchall()
        return render_template('dashboard_student.html', rooms=rooms, already_requested=already_requested)
    
