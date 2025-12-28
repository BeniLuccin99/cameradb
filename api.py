#!/usr/bin/env python3
"""Camera Streaming API for Next.js - REST API Backend"""
import os
import cv2
import threading
import time
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|loglevel;quiet'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-key')

try:
    from camera_manager import CameraManager
    USE_DATABASE = True
except:
    USE_DATABASE = False
    logger.warning("Database not available")

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
                user=self.username, password=self.password, ip=self.ip,
                port=self.port, channel=channel,
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

camera_streams = {}

def init_cameras():
    if not USE_DATABASE:
        return
    try:
        manager = CameraManager()
        cameras = manager.get_all_cameras()
        manager.close()
        
        for cam in cameras:
            stream = CameraStream(
                camera_id=cam.id, name=cam.name, ip=cam.ip_address,
                username=cam.username, password=cam.password,
                port=cam.port, stream_type='sub', fps_limit=15
            )
            if stream.connect():
                stream.start()
            camera_streams[cam.id] = stream
            logger.info(f"Initialized: {cam.name}")
    except Exception as e:
        logger.error(f"Init error: {e}")

# ==================== API ENDPOINTS ====================

@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get all cameras"""
    if not USE_DATABASE:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        manager = CameraManager()
        cameras = manager.get_all_cameras()
        manager.close()
        
        result = []
        for cam in cameras:
            result.append({
                'id': cam.id,
                'name': cam.name,
                'ip_address': cam.ip_address,
                'username': cam.username,
                'port': cam.port,
                'is_active': cam.is_active,
                'stream_url': f'/api/stream/{cam.id}',
                'is_connected': camera_streams.get(cam.id, {}).is_connected if cam.id in camera_streams else False,
                'fps': round(camera_streams[cam.id].fps, 2) if cam.id in camera_streams else 0
            })
        
        return jsonify({'cameras': result, 'count': len(result)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<int:camera_id>', methods=['GET'])
def get_camera(camera_id):
    """Get single camera"""
    if not USE_DATABASE:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        manager = CameraManager()
        cam = manager.get_camera_by_id(camera_id)
        manager.close()
        
        if not cam:
            return jsonify({'error': 'Camera not found'}), 404
        
        return jsonify({
            'id': cam.id,
            'name': cam.name,
            'ip_address': cam.ip_address,
            'username': cam.username,
            'port': cam.port,
            'is_active': cam.is_active,
            'stream_url': f'/api/stream/{cam.id}',
            'is_connected': camera_streams.get(cam.id, {}).is_connected if cam.id in camera_streams else False
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras', methods=['POST'])
def create_camera():
    """Add new camera"""
    if not USE_DATABASE:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json()
        
        manager = CameraManager()
        cam = manager.add_camera(
            name=data.get('name'),
            ip_address=data.get('ip_address'),
            username=data.get('username'),
            password=data.get('password'),
            port=int(data.get('port', 554))
        )
        manager.close()
        
        # Start stream
        stream = CameraStream(
            camera_id=cam.id, name=cam.name, ip=cam.ip_address,
            username=cam.username, password=cam.password,
            port=cam.port, stream_type='sub', fps_limit=15
        )
        if stream.connect():
            stream.start()
        camera_streams[cam.id] = stream
        
        return jsonify({
            'id': cam.id,
            'name': cam.name,
            'ip_address': cam.ip_address,
            'stream_url': f'/api/stream/{cam.id}',
            'message': 'Camera added successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/cameras/<int:camera_id>', methods=['DELETE'])
def delete_camera_api(camera_id):
    """Delete camera"""
    if not USE_DATABASE:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        if camera_id in camera_streams:
            camera_streams[camera_id].stop()
            del camera_streams[camera_id]
        
        manager = CameraManager()
        success = manager.delete_camera(camera_id)
        manager.close()
        
        if success:
            return jsonify({'message': 'Camera deleted successfully'}), 200
        return jsonify({'error': 'Camera not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/stream/<int:camera_id>')
def stream_camera(camera_id):
    """MJPEG stream endpoint"""
    if camera_id in camera_streams:
        return Response(camera_streams[camera_id].generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    return jsonify({'error': 'Camera not found'}), 404

@app.route('/api/health')
def health():
    """Health check"""
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
        'total_cameras': len(camera_streams),
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'name': 'Camera Streaming API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/cameras': 'Get all cameras',
            'GET /api/cameras/:id': 'Get single camera',
            'POST /api/cameras': 'Add new camera',
            'DELETE /api/cameras/:id': 'Delete camera',
            'GET /api/stream/:id': 'MJPEG video stream',
            'GET /api/health': 'Health check'
        }
    }), 200

if __name__ == '__main__':
    logger.info("Starting Camera Streaming API...")
    init_cameras()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
