# DayFlow HRMS

**DayFlow HRMS** is a robust and modern Human Resource Management System designed to streamline employee management, attendance tracking, payroll processing, and leave management for companies. Built with **Flask** and **MySQL**, it offers a secure and user-friendly interface for both Administrators and Employees.

## 🚀 Key Features

### 🔐 Advanced Authentication
*   **Company Registration**: Secure sign-up process for Company Administrators.
*   **Auto-Generated Credentials**: Automatically generates unique **Login IDs** (e.g., `TEJADO20250001`) and passwords for new employees.
*   **Dual Login**: Support for logging in via **Email** or **Login ID**.

### 👨‍💼 Admin Dashboard
*   **Employee Management**: View, Edit, and Add new employees with ease.
*   **Attendance Monitoring**: Real-time view of "Who's In Today" and historical attendance logs.
*   **Leave Management**: Review, Approve, or Reject employee leave requests with comments.
*   **Payroll Processing**: Generate monthly payslips, calculating net salary with bonuses and deductions.

### 👩‍💻 Employee Dashboard
*   **Personal Profile**: Manage contact details and view employment info.
*   **Attendance**: Simple **Clock In** and **Clock Out** functionality.
*   **Leave Application**: Easy form to request time off.
*   **Payroll History**: View past salary slips and payment status.
*   **Statistics**: Quick overview of remaining leaves and attendance stats.

## 🛠️ Technology Stack
*   **Backend**: Python (Flask)
*   **Database**: MySQL
*   **Frontend**: HTML5, CSS3 (Custom Premium UI), JavaScript
*   **Design**: Responsive and modern interface with refined typography and color palettes.

## ⚙️ Setup & Installation

1.  **Prerequisites**:
    *   Python 3.x
    *   MySQL Server

2.  **Install Dependencies**:
    ```bash
    pip install flask flask-mysqldb
    ```

3.  **Database Configuration**:
    *   Update the database connection details in `dayflow_hrms/db.py` or `app.py`.
    *   The application will automatically initialize the required tables (`users`, `attendance`, `leaves`, `payroll`) on the first run.

4.  **Run the Application**:
    ```bash
    cd dayflow_hrms
    python app.py
    ```
    The server will start at `http://127.0.0.1:5000`.

## 📖 Usage Guide
1.  **First Run**: Register a new Company Account. You will be assigned the **Admin** role.
2.  **Adding Employees**: Log in as Admin -> Go to Dashboard -> Click **"+ Add Employee"** (or use the form) to create accounts.
3.  **Employee Access**: Share the auto-generated Login ID and Password with the employee. They can then log in to mark attendance and view their portal.
