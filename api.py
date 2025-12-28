#!/usr/bin/env python3
"""Camera Streaming API for Render.com"""
import os
import cv2
import threading
import time
from flask import Flask, Response, jsonify, render_template
from flask_cors import CORS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress OpenCV warnings
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|loglevel;quiet'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Camera configuration from environment
CAMERA_IP = os.getenv('CAMERA_IP', '192.168.0.100')
CAMERA_USER = os.getenv('CAMERA_USER', 'admin')
CAMERA_PASS = os.getenv('CAMERA_PASS', 'OCASTA')
CAMERA_PORT = int(os.getenv('CAMERA_PORT', '554'))
STREAM_TYPE = os.getenv('STREAM_TYPE', 'sub')
FPS_LIMIT = int(os.getenv('FPS_LIMIT', '15'))

RTSP_TEMPLATES = [
    "rtsp://{user}:{password}@{ip}:{port}/Streaming/Channels/{channel}?tcp",
    "rtsp://{user}:{password}@{ip}:{port}/h264/ch1/{stream}/av_stream",
]
CHANNELS = {'main': '101', 'sub': '102'}

class CameraStream:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.is_connected = False
        self.lock = threading.Lock()
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        self.running = False
    
    def get_rtsp_urls(self):
        channel = CHANNELS[STREAM_TYPE]
        urls = []
        for template in RTSP_TEMPLATES:
            url = template.format(
                user=CAMERA_USER,
                password=CAMERA_PASS,
                ip=CAMERA_IP,
                port=CAMERA_PORT,
                channel=channel,
                stream='main_stream' if STREAM_TYPE == 'main' else 'sub_stream'
            )
            urls.append(url)
        return urls
    
    def connect(self):
        urls = self.get_rtsp_urls()
        for url in urls:
            try:
                logger.info(f"Connecting to camera...")
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                cap.set(cv2.CAP_PROP_FPS, FPS_LIMIT)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        logger.info(f"Camera connected! Resolution: {frame.shape[1]}x{frame.shape[0]}")
                        self.cap = cap
                        self.is_connected = True
                        return True
                    cap.release()
            except Exception as e:
                logger.error(f"Connection error: {e}")
        
        logger.warning("Camera connection failed")
        self.is_connected = False
        return False
    
    def start(self):
        if self.running:
            return
        self.running = True
        thread = threading.Thread(target=self._read_frames, daemon=True)
        thread.start()
        logger.info("Camera stream thread started")
    
    def _read_frames(self):
        while self.running:
            if not self.cap or not self.cap.isOpened():
                if self.connect():
                    continue
                time.sleep(5)
                continue
            
            ret, frame = self.cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                if w > 800:
                    frame = cv2.resize(frame, (800, int(h * 800 / w)), interpolation=cv2.INTER_AREA)
                
                self.frame_count += 1
                if self.frame_count % 30 == 0:
                    self.fps = self.frame_count / (time.time() - self.start_time)
                
                cv2.putText(frame, f"LIVE - {CAMERA_IP}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                with self.lock:
                    self.frame = frame
                
                time.sleep(1.0 / FPS_LIMIT)
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
            
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
            
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(1.0 / FPS_LIMIT)
    
    def _placeholder(self):
        import numpy as np
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, "Camera Disconnected", (150, 220),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(img, "Connecting...", (200, 260),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return img

camera = CameraStream()

@app.route('/')
def index():
    return render_template('index.html', camera_ip=CAMERA_IP)

@app.route('/video_feed')
def video_feed():
    return Response(camera.generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'camera_connected': camera.is_connected,
        'camera_ip': CAMERA_IP,
        'fps': round(camera.fps, 2)
    }), 200

@app.route('/api/status')
def status():
    return jsonify({
        'camera_ip': CAMERA_IP,
        'is_connected': camera.is_connected,
        'fps': round(camera.fps, 2),
        'stream_type': STREAM_TYPE
    })

if __name__ == '__main__':
    logger.info("Starting Camera Streaming API...")
    camera.connect()
    camera.start()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
