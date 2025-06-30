from flask import Flask, render_template, jsonify
import mysql.connector
import serial
import serial.tools.list_ports
from datetime import datetime
import threading
import time

app = Flask(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'GirI!2329',  # Change to a secure password
    'database': 'earth_quake_detection'
}


# Secret key for session management
app.secret_key = 'eq@123'

# Global variables with thread lock
data_lock = threading.Lock()
data_points = {
    'timestamps': [],
    'x_values': [],
    'y_values': [],
    'z_values': [],
    'magnitudes': [],
    'status': 'Normal'
}
def list_serial_ports():
    """List all available serial ports"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def find_arduino_port():
    """Try to automatically find the Arduino port"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'Arduino' in port.description or 'CH340' in port.description or 'USB Serial' in port.description:
            return port.device
    return None

def insert_into_db(timestamp, x_value, y_value, z_value, magnitude, status):
    """Insert sensor data into MySQL table"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)  # Establish a new connection
        cursor = conn.cursor()
        query = """INSERT INTO sensor_data (timestamp, x_value, y_value, z_value, magnitude, status) 
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (timestamp, x_value, y_value, z_value, magnitude, status))
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Data inserted into MySQL successfully!")
    except mysql.connector.Error as e:
        print(f"⚠️ Database Error: {e}")

def read_serial():
    global data_points
    while True:
        try:
            port = find_arduino_port()
            if not port:
                available_ports = list_serial_ports()
                print("\nAvailable ports:")
                for i, port in enumerate(available_ports):
                    print(f"{i}: {port}")
                port_index = int(input("\nSelect port number: "))
                port = available_ports[port_index]

            print(f"\nTrying to connect to {port}...")
            ser = serial.Serial(port, 9600, timeout=1)
            print(f"✅ Successfully connected to {port}")

            while True:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        print(f"🔹 Raw Serial Data: {line}")
                        try:
                            # Parse each part and extract numeric value
                            values = []
                            for part in line.split('|'):
                                # Find first numeric value (including negative sign)
                                value = ''
                                found_digit = False
                                for char in part:
                                    if char == '-' or char.isdigit():
                                        value += char
                                        found_digit = True
                                    elif found_digit and not char.isdigit():
                                        break
                                values.append(int(value))

                            x_val, y_val, z_val, mag_val = values

                            status = 'Earthquake' if 'Earthquake' in line else 'Normal'
                            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                            with data_lock:
                                data_points['timestamps'].append(current_time)
                                data_points['x_values'].append(x_val)
                                data_points['y_values'].append(y_val)
                                data_points['z_values'].append(z_val)
                                data_points['magnitudes'].append(mag_val)
                                data_points['status'] = status

                                max_points = 50
                                for key in ['timestamps', 'x_values', 'y_values', 'z_values', 'magnitudes']:
                                    if len(data_points[key]) > max_points:
                                        data_points[key] = data_points[key][-max_points:]
                            # Insert into database
                            insert_into_db(current_time, x_val, y_val, z_val, mag_val, status)

                            print(f"✅ Processed Data: X:{x_val}, Y:{y_val}, Z:{z_val}, Mag:{mag_val}, Status: {status}")
                        except Exception as e:
                            print(f"⚠️ Error processing line: {e}")
                            continue
        except serial.SerialException as e:
            print(f"\n⚠️ Serial Error: {e}")
            time.sleep(5)




@app.route('/')
def index():
    return render_template('test.html')


@app.route('/data')
def get_data():
    with data_lock:
        return jsonify({
            'timestamp': data_points['timestamps'],
            'x_values': data_points['x_values'],
            'y_values': data_points['y_values'],
            'z_values': data_points['z_values'],
            'magnitude': data_points['magnitudes'],
            'status': data_points['status']
        })


if __name__ == '__main__':
    print("Starting Earthquake Monitor...")
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()
    app.run(debug=True, use_reloader=False)