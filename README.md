# Hostel Management System (Flask)

A web-based Hostel Management System built with Flask and SQLite. This project allows admins to manage students, rooms, bookings, and complaints, while students can register, book rooms, and submit complaints.

## Project Structure

```
Hostel-Management/
├── app.py
├── db.py
├── hostel.db
├── routes/
│   ├── admin_routes.py
│   ├── routes.py
│   ├── student_routes.py
│   └── __pycache__/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── student_dashboard.js
├── templates/
│   ├── base.html
│   ├── dashboard_admin.html
│   ├── dashboard_student.html
│   ├── handle_complaints.html
│   ├── login.html
│   ├── manage_rooms.html
│   ├── my_allocation.html
│   ├── register_student.html
│   ├── submit_complaint.html
│   ├── view_bookings.html
│   └── view_students.html
└── README.md
```

## Features
- Admin and student login
- Student registration
- Room management (add, view, update status)
- Booking management (request, approve, reject)
- Complaint management
- Allocation tracking

## Requirements
- Python 3.8+
- Flask
- SQLite3

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Rohit242524/Hostel-Management.git
   cd Hostel-Management
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install requirements.txt
   ```

4. **Set up the database**
   - If `hostel.db` does not exist, create it and set up the required tables. You can use the provided `db.py` or run the schema manually.

5. **Run the application**
   ```bash
   python app.py
   ```
   The app will be available at `http://127.0.0.1:5000/`

## Usage
- Visit the login page to log in as an admin or student.
- Admins can manage rooms, view students, process bookings, and handle complaints.
- Students can register, book rooms, view their allocation, and submit complaints.

## Notes
- Make sure to update the admin credentials directly in the database for first-time use.
- Static files (CSS/JS) are in the `static/` directory.
- Templates are in the `templates/` directory.

## License
This project is for educational purposes.
