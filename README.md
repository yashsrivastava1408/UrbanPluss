# 🌆 UrbanPulse – Smart Traffic & Accident Management System  

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask App](https://img.shields.io/badge/Framework-Flask-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-ffdd00?logo=opencv&logoColor=black)](https://github.com/ultralytics/ultralytics)
[![TailwindCSS](https://img.shields.io/badge/UI-TailwindCSS-38B2AC?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Twilio](https://img.shields.io/badge/API-Twilio-EA4335?logo=twilio&logoColor=white)](https://www.twilio.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> An AI-powered system for **real-time traffic control**, **accident detection**, and **emergency response automation** using **YOLOv8**, **Flask**, and **Twilio API**.

---

## 📸 Overview  

**UrbanPulse** leverages **computer vision** and **automation** to bring intelligence to urban traffic systems.  
It dynamically controls signal timing based on vehicle density, detects accidents from video feeds,  
and triggers emergency calls with siren alerts — providing rapid response capability.

---

## 🚀 Features  

✅ **Adaptive Traffic Control** – YOLOv8 detects vehicles and optimizes signal durations  
✅ **Accident Detection System** – Identifies collisions using bounding-box overlaps  
✅ **Emergency Response** – Auto-initiates calls via Twilio Voice API  
✅ **Interactive Dashboard** – Live feed, stats, and visual alerts  
✅ **Webcam + Pre-recorded Video** support  
✅ **Siren & Full-screen Red Alert** on accident detection  

---

## 🧠 Tech Stack  

| Category | Technologies |
|-----------|--------------|
| **Frontend** | HTML5, CSS3, JavaScript (ES6), TailwindCSS |
| **Backend** | Flask, Flask-CORS, Python 3 |
| **AI / CV** | YOLOv8 (Ultralytics), OpenCV, NumPy |
| **Automation** | Twilio API (Voice Call Service) |
| **Tools** | VS Code, Git & GitHub, Virtual Env |


---

## 📂 Project Structure  

UrbanPulse/
│── app.py                     # Flask backend (traffic, accident, emergency call)
│── index.html                 # Frontend UI
│── style.css                  # Tailwind + custom CSS
│── script.js                  # Frontend logic & API handlers
│── requirements.txt           # Python dependencies
│── README.md                  # Documentation
│
├── assets/
│   ├── traffic_video.mp4       # Demo traffic video
│   ├── accident_video.mp4      # Demo accident video
│   ├── siren.mp3               # Emergency siren audio
│   └── images…               # Optional visuals
│
├── models/
│   └── yolov8n.pt              # YOLOv8 pretrained model
│
└── static/                     # Optional static resources



---

## ⚙️ Installation & Setup  

### 1️⃣ Clone the Repository  
```bash
git clone https://github.com/yashsrivastava1408/UrbanPulse.git
cd UrbanPulse

python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
pip install -r requirements.txt

4️⃣ Add Required Files
	•	models/yolov8n.pt → YOLOv8 model file
	•	assets/traffic_video.mp4 → Traffic video
	•	assets/accident_video.mp4 → Accident video


Start Flask Backend
python app.py

Open Frontend

Open index.html in any browser to access:
	•	🔹 Login → Dashboard
	•	🔹 Traffic Management
	•	🔹 Accident Detection
	•	🔹 Emergency Call System


  
