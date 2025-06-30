from flask import *
import numpy as np
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import serial
import serial.tools.list_ports
from datetime import datetime, timedelta
import threading
import time
import os
from flask_mail import Mail, Message
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from twilio.rest import Client
alert_count = 0  # Global counter for total alerts
alert_count_lock = threading.Lock()  # Lock to ensure thread safety


app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306  # MySQL username
app.config['MYSQL_USER'] = 'root'  # MySQL username
app.config['MYSQL_PASSWORD'] = 'GirI!2329'  # MySQL password
app.config['MYSQL_DB'] = 'earth_quake_detection'  # MySQL database name

mysql = MySQL(app)

# Secret key for session management
app.secret_key = 'eq@123'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'girivardhan2301@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'zfif hnof xpkc etzc'        # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'girivardhan2301@gmail.com'  # Default sender email

mail = Mail(app)

# 🔹 Twilio Configuration (Replace with your Twilio credentials)
TWILIO_ACCOUNT_SID = "AC66a6a6db8198fdfbf79d409916ae6bdb"
TWILIO_AUTH_TOKEN = "f78f95ffa62cea5a2c3b8caa54864f32"
TWILIO_PHONE_NUMBER = "+18142564991"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

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
data_lock1 = threading.Lock()
data_points1 = {
    'timestamps': [],
    'x_values': [],
    'y_values': [],
    'z_values': [],
    'magnitudes': [],
    'status': 'Normal',
    'all_timestamps': [],
    'forecast_magnitudes': [],
    'combined_timestamps': [],
    'combined_magnitudes': []
}

model = None
scaler = MinMaxScaler(feature_range=(0, 1))
sequence_length = 10

def initialize_lstm_model():
    """Initialize and compile LSTM model"""
    global model
    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(50, activation='relu', input_shape=(sequence_length, 1), return_sequences=True),
        tf.keras.layers.LSTM(30, activation='relu'),
        tf.keras.layers.Dense(37)  # Output 37 time steps (3 hours in 5-min intervals)
    ])
    model.compile(optimizer='adam', loss='mse')

    # Create some initial training data if no real data available
    if not os.path.exists('lstm_model.h5'):
        print("Training initial LSTM model...")
        X = np.random.normal(2, 1, (100, sequence_length))
        y = np.random.normal(2, 1, (100, 37))
        model.fit(X.reshape(-1, sequence_length, 1), y, epochs=5, verbose=0)
        model.save('lstm_model.h5')
    else:
        model = tf.keras.models.load_model('lstm_model.h5')



def generate_forecast_timestamps():
    """Generate timestamps for 3-hour forecast at 5-min intervals"""
    current_time = datetime.now()
    # Round to next 5 minutes
    current_time = current_time + timedelta(
        minutes=5 - current_time.minute % 5,
        seconds=-current_time.second,
        microseconds=-current_time.microsecond
    )
    timestamps = []
    for i in range(37):  # 3 hours in 5-min intervals
        future_time = current_time + timedelta(minutes=5 * i)
        timestamps.append(future_time.strftime('%H:%M'))

    return timestamps


def generate_forecast(current_magnitude):
    global model, scaler
    if model is None:
        initialize_lstm_model()
    sequence = data_points1['magnitudes'][-sequence_length:] if len(data_points1['magnitudes']) >= sequence_length else [current_magnitude] * sequence_length
    sequence_normalized = scaler.fit_transform(np.array(sequence).reshape(-1, 1))
    input_sequence = sequence_normalized.reshape(1, sequence_length, 1)
    forecast_normalized = model.predict(input_sequence, verbose=0)[0]
    forecast = scaler.inverse_transform(forecast_normalized.reshape(-1, 1)).flatten()
    forecast = np.clip(forecast, 0, 20)  # Clip values between 0 and 20
    forecast = np.convolve(forecast, np.ones(3) / 3, mode='valid')
    variations = np.random.normal(0, 0.1, len(forecast))
    forecast = forecast + variations
    forecast = np.round(forecast, 2)
    if len(forecast) < 37:
        forecast = np.pad(forecast, (0, 37 - len(forecast)), 'edge')
    else:
        forecast = forecast[:37]
    # Get forecast timestamps
    forecast_times = generate_forecast_timestamps()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return forecast.tolist()

last_alert_time = None  # Stores the last time an alert was sent
alert_cooldown = timedelta(minutes=5)  # Cooldown period for alerts (5 minutes)


def store_sensor_data(timestamp, x_value, y_value, z_value, magnitude, status):
    """Store real-time sensor data in the database"""
    with app.app_context():
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO sensor_data (timestamp, x_value, y_value, z_value, magnitude, status) VALUES (%s, %s, %s, %s, %s, %s)",
                        (timestamp, x_value, y_value, z_value, magnitude, status))
            mysql.connection.commit()
            cur.close()
            print("✅ Sensor Data Stored in DB")
        except Exception as e:
            print(f"❌ Error Storing Sensor Data: {e}")


def get_users():
    """🔍 Fetch user emails and phone numbers from the database."""
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("SELECT email, phone FROM users")
        users = cur.fetchall()
        cur.close()
        return users  # Returns a list of tuples [(email, phone), ...]


def send_email_alert(magnitude):
    """📧 Sends an email alert when an earthquake is detected."""
    with app.app_context():
        users = get_users()
        recipient_emails = [user[0] for user in users]

        if not recipient_emails:
            print("⚠️ No registered users found for email alerts.")
            return

        msg = Message(
            subject="🚨 Earthquake Detected!",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=recipient_emails,
            body=f"⚠️ Alert: An Earthquake has been detected!\nMagnitude: {magnitude}\nTime: {datetime.now().strftime('%H:%M:%S')}"
        )

        try:
            mail.send(msg)
            print("✅ Email Alert Sent!")
            update_alert_count()  # Update count in DB
        except Exception as e:
            print(f"❌ Email Sending Failed: {e}")


def send_sms_alert(magnitude):
    """📱 Sends an SMS alert to all users when an earthquake is detected."""
    with app.app_context():
        users = get_users()
        recipient_numbers = [user[1] for user in users if user[1]]

        if not recipient_numbers:
            print("⚠️ No registered users found for SMS alerts.")
            return

        alert_message = f"⚠️ Earthquake Alert! Magnitude: {magnitude}, Time: {datetime.now().strftime('%H:%M:%S')}"

        for phone_number in recipient_numbers:
            try:
                message = client.messages.create(
                    body=alert_message,
                    from_=TWILIO_PHONE_NUMBER,
                    to=f"+91{phone_number}"
                )
                print(f"✅ SMS Sent to {phone_number}! SID: {message.sid}")
            except Exception as e:
                print(f"❌ SMS Sending Failed for {phone_number}: {e}")


def update_alert_count():
    """Update the alert count in the database"""
    with alert_count_lock:
        try:
            # Connect to the database
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="GirI!2329",
                database="earth_quake_detection"
            )
            cursor = conn.cursor()

            # Ensure the table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts_log (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    alert_count INT DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            # Fetch the latest alert count
            cursor.execute("SELECT alert_count FROM alerts_log ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()

            # Determine new alert count
            new_alert_count = row[0] + 1 if row else 1  # If no records, start with 1

            # Insert new alert log entry
            cursor.execute("INSERT INTO alerts_log (alert_count) VALUES (%s)", (new_alert_count,))
            conn.commit()

            print(f"✅ Alert Count Updated in DB: {new_alert_count}")

            # Close DB connection
            cursor.close()
            conn.close()

        except mysql.connector.Error as e:
            print(f"❌ Database Error: {e}")


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


def read_serial():
    """🔍 Reads sensor data from serial and detects earthquakes with cooldown."""
    global data_points, last_alert_time

    while True:
        try:
            ser = serial.Serial('COM6', 9600, timeout=1)  # Replace 'COM3' with your port
            print("✅ Connected to Serial Port")

            while True:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        print(f"🔹 Raw Serial Data: {line}")

                        try:
                            values = []
                            for part in line.split('|'):
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


                            status = 'Earthquake' if mag_val > 5 else 'Normal'
                            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  

                            with data_lock:
                                data_points['timestamps'].append(current_time)
                                data_points['x_values'].append(x_val)
                                data_points['y_values'].append(y_val)
                                data_points['z_values'].append(z_val)
                                data_points['magnitudes'].append(mag_val)
                                data_points['status'] = status
                                # Determine status
                                if mag_val > 7:
                                    status1 = 'Severe Earthquake'
                                elif mag_val > 5:
                                    status1 = 'Moderate Earthquake'
                                elif mag_val > 3:
                                    status1 = 'Minor Earthquake'
                                else:
                                    status1 = 'Normal'
                            # Store data in the database
                            store_sensor_data(current_time, x_val, y_val, z_val, mag_val, status)
                            # Current time with seconds
                            current_time1 = datetime.now()
                            current_time_str1 = current_time1.strftime('%H:%M:%S')

                            # Generate forecast timestamps and values
                            forecast_times = generate_forecast_timestamps()
                            forecast = generate_forecast(mag_val)

                            with data_lock1:
                                # Update real-time data
                                data_points1['timestamps'].append(current_time_str1)
                                data_points1['x_values'].append(x_val)
                                data_points1['y_values'].append(y_val)
                                data_points1['z_values'].append(z_val)
                                data_points1['magnitudes'].append(mag_val)
                                data_points1['status'] = status1

                                # Keep only last 30 seconds of real-time data
                                max_realtime_points = 30
                                if len(data_points1['timestamps']) > max_realtime_points:
                                    data_points1['timestamps'] = data_points1['timestamps'][-max_realtime_points:]
                                    data_points1['magnitudes'] = data_points1['magnitudes'][-max_realtime_points:]
                                    data_points1['x_values'] = data_points1['x_values'][-max_realtime_points:]
                                    data_points1['y_values'] = data_points1['y_values'][-max_realtime_points:]
                                    data_points1['z_values'] = data_points1['z_values'][-max_realtime_points:]

                                    # Update forecast data
                                data_points1['all_timestamps'] = forecast_times
                                data_points1['forecast_magnitudes'] = forecast

                                # Combine real-time and forecast data
                                data_points1['combined_timestamps'] = data_points1['timestamps'] + forecast_times
                                data_points1['combined_magnitudes'] = data_points1['magnitudes'] + [None] * len(
                                        forecast_times)

                                max_points = 50
                                for key in ['timestamps', 'x_values', 'y_values', 'z_values', 'magnitudes']:
                                    if len(data_points[key]) > max_points:
                                        data_points[key] = data_points[key][-max_points:]

                            #print(f"✅ Processed Data: X:{x_val}, Y:{y_val}, Z:{z_val}, Mag:{mag_val}, Status: {status}")

                            # 🚨 Check Cooldown Period Before Sending Alert
                            now = datetime.now()
                            if status == "Earthquake" and (last_alert_time is None or now - last_alert_time > alert_cooldown):
                                last_alert_time = now  # Update last alert time
                                send_email_alert(mag_val)
                                send_sms_alert(mag_val)

                        except Exception as e:
                            print(f"⚠️ Error processing line: {e}")
        except serial.SerialException as e:
            print(f"\n⚠️ Serial Error: {e}")
            time.sleep(5)  # Retry connection


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        # Input validation
        if not all([name, email, phone, password]):
            flash('Please fill in all fields', 'error')
            return redirect(url_for('register'))

        cur = mysql.connection.cursor()

        # Check if email already exists
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()

        if user:
            flash('Email already exists', 'error')
            return redirect(url_for('register'))

        # Create new user
        hashed_password = generate_password_hash(password)
        cur.execute(
            'INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)',
            (name, email, phone, hashed_password)
        )
        mysql.connection.commit()
        cur.close()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the user is an admin
        if email == "admin@gmail.com" and password == "admin":
            session['logged_in'] = True
            session['is_admin'] = True
            #flash('Admin Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))


        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[4], password):
            session['logged_in'] = True
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['email'] = user[2]
            session['phone']= user[3]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    # Ensure only admin can access
    if 'logged_in' not in session or not session.get('is_admin'):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    # Get total number of users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Get total number of alerts sent
    cursor.execute("SELECT COUNT(*) FROM users")
    total_alerts = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM users ORDER BY registered_on DESC")
    users = cursor.fetchall()

    cursor.close()

    return render_template('admin_dashboard.html', users=users, total_users=total_users, total_alerts=total_alerts)



@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    print(session)
    return render_template('dashboard.html', name=session['name'], email=session['email'])


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

@app.route('/predication')
def predication():
    return render_template('predication.html')

@app.route('/predict_data')
def predict_data():
    with data_lock1:
        return jsonify(data_points1)

@app.route('/profile')
def profile():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", [session['user_id']])
    user = cursor.fetchone()
    cursor.close()
    print(user)
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    print("Starting Earthquake Monitor...")
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()
    app.run(debug=True, use_reloader=False)