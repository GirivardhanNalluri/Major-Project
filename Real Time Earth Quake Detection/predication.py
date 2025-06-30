import threading
import serial
import serial.tools.list_ports
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
import time

app = Flask(__name__)

# Global data storage
data_lock = threading.Lock()
data_points = {
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

# Initialize LSTM model and scaler
model = None
scaler = MinMaxScaler(feature_range=(0, 1))
sequence_length = 10  # Number of time steps to use for prediction


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
    """Generate 3-hour magnitude forecast using LSTM"""
    global model, scaler

    if model is None:
        initialize_lstm_model()

    # Prepare input sequence
    sequence = data_points['magnitudes'][-sequence_length:] if len(data_points['magnitudes']) >= sequence_length else [
                                                                                                                          current_magnitude] * sequence_length

    # Normalize the sequence
    sequence_normalized = scaler.fit_transform(np.array(sequence).reshape(-1, 1))

    # Reshape for LSTM input [samples, time steps, features]
    input_sequence = sequence_normalized.reshape(1, sequence_length, 1)

    # Generate forecast
    forecast_normalized = model.predict(input_sequence, verbose=0)[0]

    # Inverse transform the forecast
    forecast = scaler.inverse_transform(forecast_normalized.reshape(-1, 1)).flatten()

    # Ensure forecast values are within reasonable range
    forecast = np.clip(forecast, 0, 20)  # Clip values between 0 and 20

    # Smooth the forecast
    forecast = np.convolve(forecast, np.ones(3) / 3, mode='valid')

    # Add some minor random variations to make it more realistic
    variations = np.random.normal(0, 0.1, len(forecast))
    forecast = forecast + variations

    # Round to 2 decimal places
    forecast = np.round(forecast, 2)

    # Ensure we have exactly 37 values
    if len(forecast) < 37:
        forecast = np.pad(forecast, (0, 37 - len(forecast)), 'edge')
    else:
        forecast = forecast[:37]

    return forecast.tolist()


def read_serial():
    """Reads sensor data from serial and processes it with forecasting"""
    while True:
        try:
            ser = serial.Serial('COM6', 9600, timeout=1)
            print("✅ Connected to Serial Port")

            while True:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
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

                            # Determine status
                            if mag_val > 7:
                                status = 'Severe Earthquake'
                            elif mag_val > 5:
                                status = 'Moderate Earthquake'
                            elif mag_val > 3:
                                status = 'Minor Earthquake'
                            else:
                                status = 'Normal'

                            # Current time with seconds
                            current_time = datetime.now()
                            current_time_str = current_time.strftime('%H:%M:%S')

                            # Generate forecast timestamps and values
                            forecast_times = generate_forecast_timestamps()
                            forecast = generate_forecast(mag_val)

                            with data_lock:
                                # Update real-time data
                                data_points['timestamps'].append(current_time_str)
                                data_points['x_values'].append(x_val)
                                data_points['y_values'].append(y_val)
                                data_points['z_values'].append(z_val)
                                data_points['magnitudes'].append(mag_val)
                                data_points['status'] = status

                                # Keep only last 30 seconds of real-time data
                                max_realtime_points = 30
                                if len(data_points['timestamps']) > max_realtime_points:
                                    data_points['timestamps'] = data_points['timestamps'][-max_realtime_points:]
                                    data_points['magnitudes'] = data_points['magnitudes'][-max_realtime_points:]
                                    data_points['x_values'] = data_points['x_values'][-max_realtime_points:]
                                    data_points['y_values'] = data_points['y_values'][-max_realtime_points:]
                                    data_points['z_values'] = data_points['z_values'][-max_realtime_points:]

                                # Update forecast data
                                data_points['all_timestamps'] = forecast_times
                                data_points['forecast_magnitudes'] = forecast

                                # Combine real-time and forecast data
                                data_points['combined_timestamps'] = data_points['timestamps'] + forecast_times
                                data_points['combined_magnitudes'] = data_points['magnitudes'] + [None] * len(
                                    forecast_times)

                            print(f"✅ Processed Data: Mag:{mag_val}, Status: {status}")

                        except Exception as e:
                            print(f"⚠️ Error processing line: {e}")

        except serial.SerialException as e:
            print(f"⚠️ Serial Error: {e}")
            time.sleep(5)


@app.route('/')
def index():
    return render_template('predication.html')


@app.route('/data')
def get_data():
    with data_lock:
        return jsonify(data_points)


if __name__ == '__main__':
    print("Starting Enhanced Earthquake Monitor...")
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()
    app.run(debug=True, use_reloader=False)