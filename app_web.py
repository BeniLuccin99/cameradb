#!/usr/bin/env python3
"""Multi-Camera Web Stream - Database Integration"""
import os
import cv2
import threading
import time
from flask import Flask, Response, render_template, jsonify, request, redirect, url_for
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|loglevel;quiet'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-key')

# Import database
try:
    from camera_manager import CameraManager
    USE_DATABASE = True
except:
    USE_DATABASE = False
    logger.warning("Database not available, using in-memory storage")

RTSP_TEMPLATES = [
    "rtsp://{user}:{password}@{ip}:{port}/Streaming/Channels/{channel}?tcp",
    "rtsp://{user}:{password}@{ip}:{port}/h264/ch1/{stream}/av_stream",
]
CHANNELS = {'main': '101', 'sub': '102'}

class CameraStream:
    def __init__(self, camera_id, name, ip, username, password, port=554, stream_type='sub', fps_limit=15):
        self.camera_id = camera_id
        self.name = name
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.stream_type = stream_type
        self.fps_limit = fps_limit
        self.cap = None
        self.frame = None
        self.is_connected = False
        self.lock = threading.Lock()
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        self.running = False
    
    def get_rtsp_urls(self):
        channel = CHANNELS[self.stream_type]
        urls = []
        for template in RTSP_TEMPLATES:
            url = template.format(
                user=self.username,
                password=self.password,
                ip=self.ip,
                port=self.port,
                channel=channel,
                stream='main_stream' if self.stream_type == 'main' else 'sub_stream'
            )
            urls.append(url)
        return urls
    
    def connect(self):
        urls = self.get_rtsp_urls()
        for url in urls:
            try:
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                cap.set(cv2.CAP_PROP_FPS, self.fps_limit)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        logger.info(f"[{self.name}] Connected!")
                        self.cap = cap
                        self.is_connected = True
                        return True
                    cap.release()
            except Exception as e:
                logger.error(f"[{self.name}] Error: {e}")
        
        self.is_connected = False
        return False
    
    def start(self):
        if self.running:
            return
        self.running = True
        thread = threading.Thread(target=self._read_frames, daemon=True)
        thread.start()
    
    def _read_frames(self):
        while self.running:
            if not self.cap or not self.cap.isOpened():
                logger.warning(f"[{self.name}] Reconnecting...")
                if self.connect():
                    continue
                time.sleep(3)
                continue
            
            ret, frame = self.cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                if w > 800:
                    frame = cv2.resize(frame, (800, int(h * 800 / w)), interpolation=cv2.INTER_AREA)
                
                self.frame_count += 1
                if self.frame_count % 30 == 0:
                    self.fps = self.frame_count / (time.time() - self.start_time)
                
                cv2.putText(frame, f"{self.name}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                
                with self.lock:
                    self.frame = frame
                
                time.sleep(1.0 / self.fps_limit)
            else:
                time.sleep(0.1)
    
    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None
    
    def generate_frames(self):
        while True:
            frame = self.get_frame()
            if frame is None:
                frame = self._placeholder()
            
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue
            
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(1.0 / self.fps_limit)
    
    def _placeholder(self):
        import numpy as np
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, f"{self.name}", (200, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(img, "Disconnected", (220, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return img
    
    def stop(self):
        self.running = False
        self.is_connected = False
        if self.cap:
            self.cap.release()
            self.cap = None

# Global camera streams
camera_streams = {}

def load_cameras_from_db():
    """Load cameras from database"""
    if not USE_DATABASE:
        return []
    
    try:
        manager = CameraManager()
        cameras = manager.get_all_cameras()
        manager.close()
        return cameras
    except Exception as e:
        logger.error(f"Failed to load cameras: {e}")
        return []

def init_cameras():
    """Initialize camera streams from database"""
    cameras = load_cameras_from_db()
    
    for cam in cameras:
        stream = CameraStream(
            camera_id=cam.id,
            name=cam.name,
            ip=cam.ip_address,
            username=cam.username,
            password=cam.password,
            port=cam.port,
            stream_type='sub',
            fps_limit=15
        )
        if stream.connect():
            stream.start()
        camera_streams[cam.id] = stream
        logger.info(f"Initialized: {cam.name}")

@app.route('/')
def index():
    cameras = load_cameras_from_db()
    return render_template('multi_camera.html', cameras=cameras)

@app.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    if camera_id in camera_streams:
        return Response(camera_streams[camera_id].generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Camera not found", 404

@app.route('/add_camera', methods=['GET', 'POST'])
def add_camera():
    if request.method == 'POST':
        if USE_DATABASE:
            try:
                manager = CameraManager()
                cam = manager.add_camera(
                    name=request.form.get('name'),
                    ip_address=request.form.get('ip'),
                    username=request.form.get('username'),
                    password=request.form.get('password'),
                    port=int(request.form.get('port', 554))
                )
                manager.close()
                
                # Start new camera stream
                stream = CameraStream(
                    camera_id=cam.id,
                    name=cam.name,
                    ip=cam.ip_address,
                    username=cam.username,
                    password=cam.password,
                    port=cam.port,
                    stream_type='sub',
                    fps_limit=15
                )
                if stream.connect():
                    stream.start()
                camera_streams[cam.id] = stream
                
                return redirect(url_for('index'))
            except Exception as e:
                return f"Error: {e}", 400
        else:
            return "Database not available", 500
    
    return render_template('add_camera.html')

@app.route('/delete_camera/<int:camera_id>', methods=['POST'])
def delete_camera(camera_id):
    if USE_DATABASE:
        try:
            # Stop stream
            if camera_id in camera_streams:
                camera_streams[camera_id].stop()
                del camera_streams[camera_id]
            
            # Delete from database
            manager = CameraManager()
            manager.delete_camera(camera_id)
            manager.close()
            
            return redirect(url_for('index'))
        except Exception as e:
            return f"Error: {e}", 400
    return "Database not available", 500

@app.route('/health')
def health():
    status = {}
    for cam_id, stream in camera_streams.items():
        status[cam_id] = {
            'name': stream.name,
            'connected': stream.is_connected,
            'fps': round(stream.fps, 2)
        }
    
    return jsonify({
        'status': 'healthy',
        'cameras': status,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    logger.info("Starting multi-camera web application...")
    init_cameras()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
