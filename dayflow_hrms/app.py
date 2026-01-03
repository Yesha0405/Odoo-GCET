from flask import Flask, render_template, request, redirect, session, url_for
from db import init_db, mysql
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'your_secret_key' # Change this for production

# Initialize Database
init_db(app)

@app.route('/')
def index():
    if 'loggedin' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        account = cursor.fetchone()
        
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['name'] = account['name']
            session['role'] = account['role']
            
            if account['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))
        else:
            msg = 'Incorrect username/password!'
            
            
    return render_template('login.html', msg=msg)

def generate_login_id(company_name, full_name, joining_date):
    # Format: [Company(2)][First(2)][Last(2)][Year][Serial(4)]
    # Example: OIJODO20220001
    
    # 1. Company Code (First 2 chars, Upper)
    comp_code = company_name[:2].upper() if company_name else 'XX'
    
    # 2. Name Codes
    names = full_name.split()
    first_code = names[0][:2].upper() if names else 'XX'
    last_code = names[-1][:2].upper() if len(names) > 1 else first_code
    
    # 3. Year
    # joining_date can be date obj or string 'YYYY-MM-DD'
    if isinstance(joining_date, str):
        year = joining_date.split('-')[0]
    else:
        year = str(joining_date.year)
        
    prefix = f"{comp_code}{first_code}{last_code}{year}"
    
    # 4. Serial
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE employee_id LIKE %s", (prefix + '%',))
    count = cursor.fetchone()[0]
    serial = str(count + 1).zfill(4)
    
    return f"{prefix}{serial}"

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        company_name = request.form['company_name']
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        role = 'admin' # Register is now for Company Admin
        
        # Today as joining date for admin
        from datetime import date
        joining_date = date.today()
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        
        if account:
            msg = 'Account already exists!'
        else:
            # Generate ID for Admin too
            employee_id = generate_login_id(company_name, name, joining_date)
            
            cursor.execute('INSERT INTO users (name, email, password, role, employee_id, company_name, phone, joining_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', 
                           (name, email, password, role, employee_id, company_name, phone, joining_date))
            mysql.connection.commit()
            msg = f'Registration Successful! Your Login ID is: {employee_id}'
            # return redirect(url_for('login')) # Stay to show ID?
            
    return render_template('register.html', msg=msg)

@app.route('/dashboard', methods=['GET', 'POST'])
def employee_dashboard():
    if 'loggedin' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        leave_type = request.form['leave_type']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']
        user_id = session['id']
        
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO leaves (user_id, leave_type, reason, start_date, end_date) VALUES (%s, %s, %s, %s, %s)', (user_id, leave_type, reason, start_date, end_date))
        mysql.connection.commit()
        
    # Fetch user leaves
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM leaves WHERE user_id = %s', (session['id'],))
    leaves = cursor.fetchall()

    # Fetch user profile to ensure we have latest data
    cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
    user = cursor.fetchone()
    
    # Fetch today's attendance
    from datetime import date
    today = date.today()
    cursor.execute('SELECT * FROM attendance WHERE user_id = %s AND date = %s', (session['id'], today))
    attendance_today = cursor.fetchone()
    
    # Fetch My Payroll
    cursor.execute('SELECT * FROM payroll WHERE user_id = %s ORDER BY year DESC, id DESC', (session['id'],))
    payroll_history = cursor.fetchall()
    
    return render_template('employee_dashboard.html', leaves=leaves, user=user, attendance=attendance_today, payrolls=payroll_history)

@app.route('/attendance/clock_in', methods=['POST'])
def clock_in():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    from datetime import date, datetime
    today = date.today()
    now = datetime.now().time()
    
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('INSERT INTO attendance (user_id, date, clock_in) VALUES (%s, %s, %s)', (session['id'], today, now))
        mysql.connection.commit()
    except:
        pass # Already clocked in
        
    return redirect(url_for('employee_dashboard'))

@app.route('/attendance/clock_out', methods=['POST'])
def clock_out():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    from datetime import date, datetime
    today = date.today()
    now = datetime.now().time()
    
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE attendance SET clock_out = %s WHERE user_id = %s AND date = %s', (now, session['id'], today))
    mysql.connection.commit()
        
    return redirect(url_for('employee_dashboard'))

@app.route('/admin/update_salary', methods=['POST'])
def update_salary():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    user_id = request.form['user_id']
    salary = request.form['salary']
    
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE users SET salary = %s WHERE id = %s', (salary, user_id))
    mysql.connection.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/generate_payroll', methods=['POST'])
def generate_payroll():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    user_id = request.form['user_id']
    month = request.form['month']
    year = request.form['year']
    bonus = float(request.form.get('bonus', 0))
    deductions = float(request.form.get('deductions', 0))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT salary FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    
    if user:
        base_salary = float(user['salary'] or 0)
        net_salary = base_salary + bonus - deductions
        
        cursor.execute('''
            INSERT INTO payroll (user_id, month, year, base_salary, bonus, deductions, net_salary, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'paid')
        ''', (user_id, month, year, base_salary, bonus, deductions, net_salary))
        mysql.connection.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    phone = request.form['phone']
    address = request.form['address']
    
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE users SET phone = %s, address = %s WHERE id = %s', (phone, address, session['id']))
    mysql.connection.commit()
    
    return redirect(url_for('employee_dashboard'))

@app.route('/admin/update_user', methods=['POST'])
def admin_update_user():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    user_id = request.form['user_id']
    name = request.form['name']
    email = request.form['email']
    role = request.form['role']
    employee_id = request.form.get('employee_id', '')
    job_title = request.form.get('job_title', '')
    phone = request.form.get('phone', '')
    address = request.form.get('address', '')
    
    cursor = mysql.connection.cursor()
    cursor.execute('''
        UPDATE users 
        SET name = %s, email = %s, role = %s, employee_id = %s, job_title = %s, phone = %s, address = %s 
        WHERE id = %s
    ''', (name, email, role, employee_id, job_title, phone, address, user_id))
    mysql.connection.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/create_employee', methods=['POST'])
def create_employee():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    joining_date = request.form['joining_date']
    
    # Get Admin's company
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT company_name FROM users WHERE id = %s', (session['id'],))
    admin_user = cursor.fetchone()
    company_name = admin_user['company_name'] if admin_user else 'XX'
    
    # Generate ID
    employee_id = generate_login_id(company_name, name, joining_date)
    
    # Generate Random Password
    import random
    import string
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    try:
        cursor.execute('INSERT INTO users (name, email, password, role, employee_id, company_name, phone, joining_date, salary) VALUES (%s, %s, %s, "employee", %s, %s, %s, %s, 0)', 
                       (name, email, password, employee_id, company_name, phone, joining_date))
        mysql.connection.commit()
        
        # In a real app, email this. Here we show it.
        # We'll use a session flash message or redirect with query params
        return render_template('admin_dashboard.html', 
                               new_employee={'name': name, 'id': employee_id, 'password': password},
                               leaves=get_leaves(), employees=get_employees(), active_employees=get_active_employees(), attendance_history=get_attendance_history()) 
                               # Note: Need helper functions for data to re-render dashboard properly or just redirect and use flash.
                               # For simplicity in this one-file setup, let's redirect to dashboard with a success message in URL or session?
                               # Better: Render a "success" intermediary page or modal?
                               # Let's simple redirect with a msg parameters if possible, but params in URL is unsafe for password.
                               # Let's stick to render_template but I need to duplicate the fetch logic.
    except Exception as e:
        return str(e) # Debug

    # Store credentials in session to display them once
    session['new_employee'] = {'name': name, 'id': employee_id, 'password': password}
    return redirect(url_for('admin_dashboard'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        leave_id = request.form['leave_id']
        status = request.form['status']
        admin_comment = request.form.get('admin_comment', '')
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE leaves SET status = %s, admin_comment = %s WHERE id = %s', (status, admin_comment, leave_id))
        mysql.connection.commit()
    
    # Check for new employee creation
    new_employee = session.pop('new_employee', None)
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT leaves.*, users.name as user_name FROM leaves JOIN users ON leaves.user_id = users.id ORDER BY leaves.id DESC')
    leaves = cursor.fetchall()
    
    cursor.execute('SELECT * FROM users WHERE role != "admin"')
    employees = cursor.fetchall()
    
    # Fetch active employees (clocked in today)
    from datetime import date
    today = date.today()
    cursor.execute('SELECT attendance.*, users.name FROM attendance JOIN users ON attendance.user_id = users.id WHERE date = %s AND clock_out IS NULL', (today,))
    active_employees = cursor.fetchall()
    active_ids = [emp['user_id'] for emp in active_employees]

    # Fetch approved leaves for today
    cursor.execute('SELECT * FROM leaves WHERE status = "Approved" AND start_date <= %s AND end_date >= %s', (today, today))
    on_leave = cursor.fetchall()
    leave_ids = [l['user_id'] for l in on_leave]

    # Process employees with status
    for emp in employees:
        if emp['id'] in active_ids:
            emp['status'] = 'present' # Green dot
        elif emp['id'] in leave_ids:
            emp['status'] = 'leave' # Airplane
        else:
            emp['status'] = 'absent' # Yellow dot

    # Fetch Admin's OWN attendance for Systray
    cursor.execute('SELECT * FROM attendance WHERE user_id = %s AND date = %s', (session['id'], today))
    my_attendance = cursor.fetchone()

    # Fetch all attendance history
    cursor.execute('SELECT attendance.*, users.name FROM attendance JOIN users ON attendance.user_id = users.id ORDER BY date DESC, clock_in DESC LIMIT 50')
    attendance_history = cursor.fetchall()
    
    return render_template('admin_dashboard.html', leaves=leaves, employees=employees, active_employees=active_employees, attendance_history=attendance_history, new_employee=new_employee)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
