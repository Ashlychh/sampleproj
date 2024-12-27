from flask import Flask, request, jsonify
import mysql.connector
import time
import socket

app = Flask(__name__)

# MySQL Database connection details
db_config = {
    "host": "localhost",
    "user": "root",  # Use your MySQL username
    "password": "your_password",  # Use your MySQL password
    "database": "adms"
}

# Utility function to connect to MySQL database
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Home Route
@app.route('/')
def home():
    return "Welcome to the Attendance Data Management System (ADMS)"

# Route to register an employee
@app.route('/register_employee', methods=['POST'])
def register_employee():
    name = request.json.get('name')
    department = request.json.get('department')
    serial_number = request.json.get('serial_number')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO employees (name, department, serial_number) VALUES (%s, %s, %s)",
                   (name, department, serial_number))
    conn.commit()
    
    cursor.close()
    conn.close()

    return jsonify({"message": "Employee registered successfully!"}), 201

# Route to mark attendance
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    employee_id = request.json.get('employee_id')
    status = request.json.get('status')  # 'in' or 'out'
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO attendance (employee_id, status) VALUES (%s, %s)",
                   (employee_id, status))
    conn.commit()
    
    cursor.close()
    conn.close()

    return jsonify({"message": "Attendance marked successfully!"}), 201

# Route to fetch attendance data for an employee
@app.route('/attendance/<int:employee_id>', methods=['GET'])
def get_attendance(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM attendance WHERE employee_id = %s", (employee_id,))
    attendance_records = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"attendance": attendance_records})

# Route to manage device status (e.g., check if the device is online)
@app.route('/device_status/<string:serial_number>', methods=['GET'])
def device_status(serial_number):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT online FROM devices WHERE serial_number = %s", (serial_number,))
    status = cursor.fetchone()

    cursor.close()
    conn.close()

    if status:
        return jsonify({"serial_number": serial_number, "online": status[0]})
    else:
        return jsonify({"message": "Device not found!"}), 404

# Function to communicate with a ZKTeco device via TCP/IP
def communicate_with_device(device_ip, device_port):
    try:
        # Establish a connection with the ZKTeco device
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((device_ip, device_port))
        
        # Send the command to the device (e.g., fetch attendance data)
        command = b'\x01\x04\x00\x00\x00\x01\x00\x01\x60\xA9'  # Example command (modify as needed)
        s.send(command)

        # Receive the data from the device
        data = s.recv(1024)  # Adjust buffer size as needed
        s.close()

        return data

    except Exception as e:
        print(f"Error communicating with device: {e}")
        return None

# Route to sync data from a ZKTeco device (example)
@app.route('/sync_device/<string:serial_number>', methods=['GET'])
def sync_device(serial_number):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch device IP and Port (you can add this info in the devices table)
    cursor.execute("SELECT device_ip, device_port FROM devices WHERE serial_number = %s", (serial_number,))
    device = cursor.fetchone()

    if device:
        device_ip, device_port = device
        data = communicate_with_device(device_ip, device_port)

        if data:
            # Process the data and store it in the database (e.g., mark attendance)
            print(f"Data received from device: {data}")

            # For simplicity, let's assume the data contains employee ID and attendance status
            employee_id = 123  # Example (you will need to parse the actual data)
            status = "in"  # Example status
            cursor.execute("INSERT INTO attendance (employee_id, status) VALUES (%s, %s)", (employee_id, status))
            conn.commit()
        
            cursor.close()
            conn.close()

            return jsonify({"message": "Device synced successfully!"})

    cursor.close()
    conn.close()
    return jsonify({"message": "Device not found!"}), 404

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

