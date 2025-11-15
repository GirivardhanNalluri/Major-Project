---

## 🌍 Real-Time Earthquake Detection and Intensity Forecasting System

This is the official repository for our **B.Tech Major Project (Batch-08)**. The system leverages IoT technology and machine learning models to detect seismic activity in real time and forecast earthquake intensity using LSTM deep learning models.

---

## 📌 Project Features

* 🔧 **IoT-based real-time seismic data collection** using Arduino + ADXL335 accelerometer
* 📈 **Machine Learning (LSTM)** model for intensity prediction
* 🌐 **Web dashboard** for visualization and alerts
* 🔔 **Email/SMS alert system** for abnormal readings
* 📊 **Data visualization**, model performance graphs & history

---

## 🗂️ Project Structure

```
Batch-08/
├── Base_Paper.pdf
├── User_Manual.pdf
├── requirements.txt
├── Code/
│   ├── Hardware/
│   │   └── Earth_quake.ino
│   └── Software/
│       ├── main.py
│       ├── alerts.py
│       ├── device.py
│       ├── model_training.py
│       ├── predication.py
│       ├── earthquake.csv
│       ├── *.h5
│       ├── templates/
│       └── static/
│           ├── css/
│           └── images/
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository:

```bash
git clone https://github.com/GirivardhanNalluri/Major-Project.git
cd Major-Project/Batch-08/Code/Software
```

### 2️⃣ Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3️⃣ Install dependencies:

```bash
pip install -r requirements.txt
```

### 4️⃣ Run the application:

```bash
python main.py
```

---

## 🖥️ Hardware Setup

* Arduino UNO
* ADXL335 Accelerometer
* USB Serial Communication
* Arduino Sketch: **Earth_quake.ino**

---

## 🤖 Machine Learning Model

* Model: **LSTM (Long Short-Term Memory)**
* Files: `earthquake_lstm_model.h5`, `lstm_model.h5`
* Trained on time-series seismic data

---

## 🛠️ Technologies Used

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python, Flask
* **Database:** MySQL
* **ML:** TensorFlow, Keras, NumPy, Pandas, Scikit-learn
* **IoT:** Arduino + ADXL335
* **Deployment:** Localhost

---

## 📚 Documentation

* 🎓 **[Base Paper](./Base_Paper.pdf)**
* 🧾 **[User Manual](./User_Manual.pdf)**
* 📝 **Published Research Paper:**
  👉 **[Click to view the Publication Paper](https://www.scilit.com/publications/575b54c1b824b23efd858ef580477e57)**


---

## 👨‍💻 Authors

**B.Tech Final Year Students – Batch-08**
**NALLURI GIRIVARDHAN**
Under the guidance of **M. TANOOJ KUMAR**

---

## 📬 Contact

*📧 Email: **[girivardhan2301@gmail.com](mailto:girivardhan2301@gmail.com)**
*🔗 LinkedIn: *[Nalluri Girivardhan](https://www.linkedin.com/in/girivardhan-nalluri-215341267)*
*💬 For issues or collaboration: **GitHub Issues**

---
