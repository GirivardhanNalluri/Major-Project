import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import time

# Serial port settings
serial_port = 'COM6'  # Replace with your actual COM port
baud_rate = 9600

# Initialize serial connection
try:
    ser = serial.Serial(serial_port, baud_rate, timeout=1)
except:
    print(f"Warning: Could not connect to {serial_port}")
    ser = None

# Data queues for X, Y, Z values
x_data = deque(maxlen=100)
y_data = deque(maxlen=100)
z_data = deque(maxlen=100)
time_data = deque(maxlen=100)  # Time axis

# Initialize time counter
time_counter = 0

# Flags for earthquake detection
earthquake_detected = False
alert_end_time = 0  # Timestamp for when the alert ends

# Last X, Y, Z values for real-time display
last_x = 0
last_y = 0
last_z = 0


def parse_serial_data(serial_line):
    """
    Parse the serial data string and extract X, Y, Z values.
    """
    global earthquake_detected, alert_end_time
    try:
        if "Earthquake Detected!" in serial_line:
            earthquake_detected = True
            alert_end_time = time.time() + 5  # Set alert duration to 5 seconds
            print("EARTHQUAKE DETECTED!")
        elif "Normal:" in serial_line:
            parts = serial_line.split('|')
            x_value = int(parts[0].split(':')[-1].strip())
            y_value = int(parts[1].split(':')[-1].strip())
            z_value = int(parts[2].split(':')[-1].strip())
            return x_value, y_value, z_value
    except (IndexError, ValueError) as e:
        print(f"Error parsing serial data: {e}")
    return None, None, None


def update_plot(frame):
    """
    Update the Matplotlib plot with new data.
    """
    global time_counter, earthquake_detected, alert_end_time, last_x, last_y, last_z

    # Read serial data
    if ser.in_waiting > 0:
        try:
            serial_line = ser.readline().decode('utf-8', errors='ignore').strip()  # Handle non-UTF-8 bytes
            print("Serial Line:", serial_line)

            x_value, y_value, z_value = parse_serial_data(serial_line)
            if x_value is not None and y_value is not None and z_value is not None:
                x_data.append(x_value)
                y_data.append(y_value)
                z_data.append(z_value)
                time_data.append(time_counter)
                time_counter += 1

                # Update the last X, Y, Z values
                last_x, last_y, last_z = x_value, y_value, z_value
        except Exception as e:
            print(f"Error reading serial data: {e}")

    # Clear axes
    ax.clear()

    # Plot X, Y, Z values with smooth curves
    ax.plot(time_data, x_data, label='X (Blue)', color='blue', linewidth=2, alpha=0.8)
    ax.plot(time_data, y_data, label='Y (Green)', color='green', linewidth=2, alpha=0.8)
    ax.plot(time_data, z_data, label='Z (Red)', color='red', linewidth=2, alpha=0.8)

    # Add earthquake alert
    if earthquake_detected:
        ax.set_title("⚠️ EARTHQUAKE DETECTED! ⚠️", fontsize=18, color='red', fontweight='bold')
        if time.time() > alert_end_time:
            earthquake_detected = False
    else:
        ax.set_title("Real-Time Earthquake Visualization", fontsize=16, color='darkblue', fontweight='bold')

    # Display real-time X, Y, Z values on the right side of the graph
    ax.text(0.92, 0.9, f"X: {last_x}", transform=ax.transAxes, fontsize=12, color='blue', fontweight='bold')
    ax.text(0.92, 0.85, f"Y: {last_y}", transform=ax.transAxes, fontsize=12, color='green', fontweight='bold')
    ax.text(0.92, 0.8, f"Z: {last_z}", transform=ax.transAxes, fontsize=12, color='red', fontweight='bold')

    # Add labels and legend
    ax.set_xlabel("Time (s)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Acceleration (G)", fontsize=12, fontweight='bold')
    ax.legend(loc="upper left", fontsize=10, frameon=True, facecolor='lightgray', edgecolor='black')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_ylim(-30, 30)  # Adjust based on your data range


# Set up Matplotlib figure and axes
fig, ax = plt.subplots(figsize=(12, 6))

# Add a background color to the plot
fig.patch.set_facecolor('#f5f5f5')
ax.set_facecolor('#ffffff')

# Create an animation
ani = animation.FuncAnimation(fig, update_plot, interval=100, cache_frame_data=False)  # Update every 100ms

# Show the plot
plt.tight_layout()
plt.show()

# Close the serial connection on exit
ser.close()