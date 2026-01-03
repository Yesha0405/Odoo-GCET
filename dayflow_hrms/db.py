import MySQLdb
from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    # Configure MySQL
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'yesha0405' # Assuming empty password as per plan
    app.config['MYSQL_DB'] = 'dayflow_hrms_db'
    
    mysql.init_app(app)
    
    with app.app_context():
        # Create DB if not exists (This requires a separate connection usually, but we'll try to rely on pre-existence or handle it gracefully)
        # Actually, flask_mysqldb connects to a specific DB. We might need to connect without DB first to create it.
        # For simplicity, let's assume the user can create the DB or we use a raw connection to create it.
        try:
            _create_database()
            _create_tables()
        except Exception as e:
            print(f"Error initializing DB: {e}")

def _create_database():
    # Connect to MySQL server directly to create database
    db = MySQLdb.connect(host="localhost", user="root", passwd="yesha0405")
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS dayflow_hrms_db")
    cursor.close()
    db.close()

def _create_tables():
    cursor = mysql.connection.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('employee', 'admin') DEFAULT 'employee',
            employee_id VARCHAR(50), -- Using this as the 'Login ID'
            company_name VARCHAR(100),
            joining_date DATE,
            phone VARCHAR(20),
            address TEXT,
            job_title VARCHAR(100),
            salary DECIMAL(10, 2) DEFAULT 0.00
        )
    ''')
    
    # Leaves table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            leave_type VARCHAR(50),
            reason TEXT,
            start_date DATE,
            end_date DATE,
            status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
            admin_comment TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            date DATE,
            clock_in TIME,
            clock_out TIME,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE KEY unique_attendance (user_id, date)
        )
    ''')

    # Payroll table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payroll (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            month VARCHAR(20),
            year INT,
            base_salary DECIMAL(10, 2),
            bonus DECIMAL(10, 2) DEFAULT 0.00,
            deductions DECIMAL(10, 2) DEFAULT 0.00,
            net_salary DECIMAL(10, 2),
            status ENUM('paid', 'pending') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Simple migration to ensure admin_comment exists if table was already created
    try:
        cursor.execute("ALTER TABLE leaves ADD COLUMN admin_comment TEXT")
    except:
        pass # Column likely already exists
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN salary DECIMAL(10, 2) DEFAULT 0.00")
    except:
        pass # Column likely already exists
        
    # Migration for new profile fields
    for col in ['employee_id VARCHAR(50) UNIQUE', 'phone VARCHAR(20)', 'address TEXT', 'job_title VARCHAR(100)', 'company_name VARCHAR(100)', 'joining_date DATE']:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col}")
        except:
            pass
    
    mysql.connection.commit()
    cursor.close()
