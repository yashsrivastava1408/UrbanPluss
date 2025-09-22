import threading
import time
import cv2
import numpy as np
from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from ultralytics import YOLO

# --- Backend Configuration ---
app = Flask(__name__)
CORS(app) 

analysis_thread = None 
frame_lock = threading.Lock() 
output_frame = None 
stop_event = threading.Event()

# Load the YOLOv8 model for object detection
model = YOLO('yolov8n.pt')

VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck

# Shared data structure to hold the latest traffic info
traffic_data = {
    "lane_A": {"vehicle_count": 0, "green_light_duration": 0},
    "lane_B": {"vehicle_count": 0, "green_light_duration": 0},
    "total_vehicles": 0
}

def reset_traffic_data():
    """Resets the traffic data to its initial state."""
    global traffic_data
    traffic_data = {
        "lane_A": {"vehicle_count": 0, "green_light_duration": 0},
        "lane_B": {"vehicle_count": 0, "green_light_duration": 0},
        "total_vehicles": 0
    }


def analyze_traffic_video(video_source):
    """
    Analyzes a video stream to count vehicles and update traffic data.
    This function runs in a separate thread.
    """
    global traffic_data, output_frame
    print(f"Video analysis thread started for source: {video_source}")
    
    # If the source is 'webcam', use camera index 0. Otherwise, use the path.
    cap_source = 0 if video_source == 'webcam' else video_source
    cap = cv2.VideoCapture(cap_source)

    if not cap.isOpened():
        print(f"Error: Could not open video source {video_source}")
        return

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("End of video stream. Restarting...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
            
        results = model(frame, stream=True, verbose=False)
        current_frame_counts = {"lane_A": 0, "lane_B": 0}

        # Define lanes based on frame dimensions
        height, width, _ = frame.shape
        lane_A_roi = [(0, 0), (width // 2, height)]
        lane_B_roi = [(width // 2, 0), (width, height)]

        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) in VEHICLE_CLASSES:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    center_x = (x1 + x2) / 2
                    
                    # Draw a red rectangle around the detected vehicle
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    
                    if center_x < width // 2:
                        current_frame_counts["lane_A"] += 1
                    else:
                        current_frame_counts["lane_B"] += 1
        
        # --- Update shared traffic data ---
        traffic_data["lane_A"]["vehicle_count"] = current_frame_counts["lane_A"]
        traffic_data["lane_B"]["vehicle_count"] = current_frame_counts["lane_B"]
        total_vehicles = current_frame_counts["lane_A"] + current_frame_counts["lane_B"]
        traffic_data["total_vehicles"] = total_vehicles

        # --- Calculate green light duration ---
        min_duration, max_duration = 10, 60
        if total_vehicles > 0:
            ratio_A = traffic_data["lane_A"]["vehicle_count"] / total_vehicles
            ratio_B = traffic_data["lane_B"]["vehicle_count"] / total_vehicles
            traffic_data["lane_A"]["green_light_duration"] = int(min_duration + ratio_A * (max_duration - min_duration))
            traffic_data["lane_B"]["green_light_duration"] = int(min_duration + ratio_B * (max_duration - min_duration))
        else:
            traffic_data["lane_A"]["green_light_duration"] = min_duration
            traffic_data["lane_B"]["green_light_duration"] = min_duration

        # --- Update the output frame for streaming ---
        with frame_lock:
            output_frame = frame.copy()

    cap.release()
    print("Video analysis thread stopped.")

def generate_video_stream():
    """Yields frames for the video stream response."""
    while True:
        with frame_lock:
            if output_frame is None:
                # If analysis hasn't started, show a placeholder
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Waiting for video source...", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                (flag, encodedImage) = cv2.imencode(".jpg", placeholder)
            else:
                # Encode the processed frame
                (flag, encodedImage) = cv2.imencode(".jpg", output_frame)

        if not flag:
            continue

        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

@app.route('/api/start-analysis', methods=['POST'])
def start_analysis():
    """Starts the video analysis thread with a source from the request."""
    global analysis_thread
    
    if analysis_thread and analysis_thread.is_alive():
        stop_event.set()
        analysis_thread.join() 
    stop_event.clear()
    reset_traffic_data()
    
    data = request.get_json()
    source = data.get('source')
    if not source:
        return jsonify({"error": "Video source not provided"}), 400

    
    video_path = "traffic_video.mp4" if source == 'prerecorded' else 'webcam'

    analysis_thread = threading.Thread(target=analyze_traffic_video, args=(video_path,), daemon=True)
    analysis_thread.start()
    
    return jsonify({"message": f"Analysis started with source: {source}"}), 200

@app.route('/api/traffic-data')
def get_traffic_data():
    """API endpoint to serve the current traffic data."""
    return jsonify(traffic_data)

@app.route('/video_feed')
def video_feed():
    """Returns the video stream response."""
    return Response(generate_video_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
    print("Starting backend services...")
    print("Ready to receive analysis start command from the frontend.")
    app.run(host='0.0.0.0', port=5001)

