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

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        role = request.form.get('role', 'employee')
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        
        if account:
            msg = 'Account already exists!'
        else:
            cursor.execute('INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)', (name, email, password, role))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            return redirect(url_for('login'))
            
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
    
    return render_template('employee_dashboard.html', leaves=leaves, user=user, attendance=attendance_today)

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

    # Fetch all attendance history
    cursor.execute('SELECT attendance.*, users.name FROM attendance JOIN users ON attendance.user_id = users.id ORDER BY date DESC, clock_in DESC LIMIT 50')
    attendance_history = cursor.fetchall()
    
    return render_template('admin_dashboard.html', leaves=leaves, employees=employees, active_employees=active_employees, attendance_history=attendance_history)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
