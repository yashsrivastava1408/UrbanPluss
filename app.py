import threading
import time
import cv2
import numpy as np
from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from ultralytics import YOLO
from twilio.rest import Client


# --- Backend Configuration ---
app = Flask(__name__)
CORS(app)

# --- YOLO Model ---
model = YOLO('yolov8n.pt')
# --- Twilio Config ---
TWILIO_ACCOUNT_SID = "xxxxxxxx"
TWILIO_AUTH_TOKEN = "xxxxxxx"
TWILIO_PHONE_NUMBER = "xxxxxx"   # your Twilio number
EMERGENCY_PHONE_NUMBER = "+xxxxxxx"  # where to call

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/api/make-call', methods=['POST'])
def make_call():
    try:
        call = client.calls.create(
            to=EMERGENCY_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER,
            url="http://demo.twilio.com/docs/voice.xml"  # voice response XML
        )
        return jsonify({"message": "Call initiated", "sid": call.sid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck

# ==============================================================================
# SECTION 1: TRAFFIC LIGHT MANAGEMENT SYSTEM
# ==============================================================================

traffic_analysis_thread = None
traffic_frame_lock = threading.Lock()
traffic_output_frame = None
traffic_stop_event = threading.Event()
traffic_data = {}
traffic_cap = None

def reset_traffic_data():
    global traffic_data
    traffic_data = {
        "lane_A": {"vehicle_count": 0, "green_light_duration": 0},
        "lane_B": {"vehicle_count": 0, "green_light_duration": 0},
        "total_vehicles": 0,
    }
reset_traffic_data()

def analyze_traffic_video(video_source):
    global traffic_cap, traffic_output_frame, traffic_data
    traffic_cap = cv2.VideoCapture(video_source)
    if not traffic_cap.isOpened():
        print(f"Error: Could not open traffic video source {video_source}")
        return

    min_duration, max_duration = 10, 60
    while not traffic_stop_event.is_set():
        ret, frame = traffic_cap.read()
        if not ret:
            traffic_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        height, width = frame.shape[:2]
        mid_x = width // 2
        current_frame_counts = {"lane_A": 0, "lane_B": 0}

        results = model(frame, stream=True, verbose=False)
        for r in results:
            for box in getattr(r, "boxes", []):
                if int(box.cls[0]) in VEHICLE_CLASSES:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    center_x = (x1 + x2) / 2
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    if center_x < mid_x:
                        current_frame_counts["lane_A"] += 1
                    else:
                        current_frame_counts["lane_B"] += 1

        traffic_data["lane_A"]["vehicle_count"] = current_frame_counts["lane_A"]
        traffic_data["lane_B"]["vehicle_count"] = current_frame_counts["lane_B"]
        total_vehicles = sum(current_frame_counts.values())
        traffic_data["total_vehicles"] = total_vehicles
        
        if total_vehicles > 0:
            ratio_A, ratio_B = current_frame_counts["lane_A"] / total_vehicles, current_frame_counts["lane_B"] / total_vehicles
        else:
            ratio_A = ratio_B = 0.5
        
        traffic_data["lane_A"]["green_light_duration"] = int(min_duration + ratio_A * (max_duration - min_duration))
        traffic_data["lane_B"]["green_light_duration"] = int(min_duration + ratio_B * (max_duration - min_duration))

        with traffic_frame_lock:
            traffic_output_frame = frame.copy()
        time.sleep(0.02)
    traffic_cap.release()

def generate_traffic_video_stream():
    while True:
        with traffic_frame_lock:
            if traffic_output_frame is None:
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Traffic Feed Offline", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                flag, encodedImage = cv2.imencode(".jpg", placeholder)
            else:
                flag, encodedImage = cv2.imencode(".jpg", traffic_output_frame)
        if not flag: continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

# ==============================================================================
# SECTION 2: ACCIDENT DETECTION SYSTEM (Using Your Logic)
# ==============================================================================

accident_analysis_thread = None
accident_frame_lock = threading.Lock()
accident_output_frame = None
accident_stop_event = threading.Event()
accident_data = {}
accident_cap = None

def reset_accident_data():
    global accident_data
    accident_data = { "accident_detected": False }
reset_accident_data()

def analyze_accident_video(video_source):
    global accident_cap, accident_output_frame, accident_data
    accident_cap = cv2.VideoCapture(video_source)
    if not accident_cap.isOpened():
        print(f"Error: Could not open accident video source {video_source}")
        return

    while not accident_stop_event.is_set():
        ret, frame = accident_cap.read()
        if not ret:
            accident_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        results = model(frame, stream=True, verbose=False)
        vehicle_boxes = []

        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) in VEHICLE_CLASSES:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    vehicle_boxes.append((x1, y1, x2, y2))
        
        # --- Your Accident Detection Logic ---
        accident = False
        for i in range(len(vehicle_boxes)):
            for j in range(i + 1, len(vehicle_boxes)):
                x1, y1, x2, y2 = vehicle_boxes[i]
                xa1, ya1, xa2, ya2 = vehicle_boxes[j]
                
                overlap_x = max(0, min(x2, xa2) - max(x1, xa1))
                overlap_y = max(0, min(y2, ya2) - max(y1, ya1))
                overlap_area = overlap_x * overlap_y
                
                if overlap_area > 5000:  # threshold
                    accident = True
                    cv2.putText(frame, "ACCIDENT DETECTED!", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        
        accident_data["accident_detected"] = accident

        with accident_frame_lock:
            accident_output_frame = frame.copy()
        time.sleep(0.02)
    
    accident_cap.release()

def generate_accident_video_stream():
    while True:
        with accident_frame_lock:
            if accident_output_frame is None:
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Accident Feed Offline", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                flag, encodedImage = cv2.imencode(".jpg", placeholder)
            else:
                flag, encodedImage = cv2.imencode(".jpg", accident_output_frame)
        if not flag: continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

# ==============================================================================
# SECTION 3: FLASK API ENDPOINTS
# ==============================================================================

# --- Traffic Light Endpoints ---
@app.route('/api/start-traffic-analysis', methods=['POST'])
def start_traffic_analysis():
    global traffic_analysis_thread, traffic_stop_event
    data = request.get_json()
    source = data.get('source')
    if source == 'prerecorded': video_path = 'traffic_video.mp4'
    elif source == 'webcam': video_path = 0
    else: return jsonify({"error": "Invalid source"}), 400

    if traffic_analysis_thread and traffic_analysis_thread.is_alive():
        traffic_stop_event.set()
        traffic_analysis_thread.join(timeout=2)
    
    traffic_stop_event.clear()
    reset_traffic_data()
    traffic_analysis_thread = threading.Thread(target=analyze_traffic_video, args=(video_path,), daemon=True)
    traffic_analysis_thread.start()
    return jsonify({"message": f"Traffic analysis started"}), 200

@app.route('/api/traffic-data')
def get_traffic_data():
    return jsonify(traffic_data)
    
@app.route('/traffic_video_feed')
def traffic_video_feed():
    return Response(generate_traffic_video_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

# --- Accident Detection Endpoints ---
@app.route('/api/start-accident-analysis', methods=['POST'])
def start_accident_analysis():
    global accident_analysis_thread, accident_stop_event
    data = request.get_json()
    source = data.get('source')
    
    if source == 'prerecorded_accident': video_path = 'accident.mp4'
    elif source == 'webcam': video_path = 0
    else: return jsonify({"error": "Invalid source"}), 400

    if accident_analysis_thread and accident_analysis_thread.is_alive():
        accident_stop_event.set()
        accident_analysis_thread.join(timeout=2)
    
    accident_stop_event.clear()
    reset_accident_data()
    accident_analysis_thread = threading.Thread(target=analyze_accident_video, args=(video_path,), daemon=True)
    accident_analysis_thread.start()
    return jsonify({"message": f"Accident analysis started"}), 200

@app.route('/api/accident-data')
def get_accident_data():
    return jsonify(accident_data)
    
@app.route('/accident_video_feed')
def accident_video_feed():
    return Response(generate_accident_video_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
    print("Starting backend services...")
    app.run(host='0.0.0.0', port=5001, debug=False)

