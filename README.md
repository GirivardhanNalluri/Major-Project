# 🌍 Real-Time Earthquake Detection and Intensity Forecasting System

This is the official repository for our B.Tech Major Project developed by Batch-08. The system leverages IoT technology and machine learning models to detect seismic activity in real time and predict earthquake intensity. It combines hardware (Arduino + sensors) and software (Python + LSTM) to provide an early warning interface.

## 📌 Project Features

- 🔧 **IoT-based real-time data collection** using an Arduino and accelerometer.
- 📈 **Machine Learning prediction** using LSTM for forecasting seismic intensity.
- 🌐 **Web-based dashboard** for monitoring alerts, graphs, and reports.
- 🔔 **Alert system** via email/SMS when abnormal activity is detected.
- 📊 Visual insights from model performance graphs and historical data.

## 🗂️ Project Structure

```
Batch-08/
├── Base_Paper.pdf
├── User_Manual.pdf
├── requirements.txt
├── Code/
│   ├── Hardware/
│   │   └── Earth_quake.ino        # Arduino sketch
│   └── Software/
│       ├── main.py                # Main app
│       ├── alerts.py              # Alert logic
│       ├── device.py              # Device interface
│       ├── model_training.py      # Model training
│       ├── predication.py         # Prediction script
│       ├── earthquake.csv         # Sample dataset
│       ├── *.h5                   # Trained ML models
│       ├── templates/             # HTML templates
│       └── static/
│           ├── css/
│           └── images/
```

## ⚙️ Setup Instructions

1. **Clone this repository:**
   ```bash
   git clone https://github.com/your-username/earthquake-detection.git
   cd earthquake-detection/Batch-08/Code/Software
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## 🖥️ Hardware Setup

- Arduino UNO
- ADXL335 accelerometer sensor
- USB serial communication with PC
- Sketch: `Earth_quake.ino` (upload via Arduino IDE)

## 🤖 Machine Learning Model

- Model: **LSTM (Long Short-Term Memory)**
- Trained on time-series earthquake data
- Stored in `earthquake_lstm_model.h5` and `lstm_model.h5`

## 🛠️ Technologies Used

- **Frontend:** HTML, CSS, Js
- **Backend:** Python, Flask
- **Database:** MySQL
- **ML Frameworks:** TensorFlow , Keras , Pandas , Numpy , Scikit-Learn
- **IoT:** Arduino, ADXL335
- **Deployment:** Localhost (for testing)
- **IDE:** Arduino IDE, PyCharm
  
## 📚 Documentation

All key documents are available in the root folder:
- 🎓 `Base_Paper.pdf`
- 🧾 `User_Manual.pdf`

## 👨‍💻 Authors

- B.Tech Final Year Students – **Batch-08 (NALLURI GIRIVARDHAN)**
- Under the guidance of [M. TANOOJ KUMAR]

Published Paper
[Paper] (https://www.scilit.com/publications/575b54c1b824b23efd858ef580477e57)

## 📬 Contact

For any queries or collaborations, feel free to reach out via GitHub issues or university email.
📧 **Email:** girivardhan2301@gmail.com 
🔗 [LinkedIn](https://www.linkedin.com/in/girivardhan-nalluri-215341267/)

