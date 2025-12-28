#!/usr/bin/env python3
"""
Dual Hikvision Camera Live Stream Application
Streams from two cameras simultaneously

Usage:
    python dual_camera_stream.py

Controls:
    'q' - Quit both streams
    's' - Save snapshots from both cameras
    'f' - Toggle FPS display
"""

import os
import sys

# Suppress FFmpeg warnings BEFORE importing cv2
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|loglevel;quiet'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

import cv2
import threading
import time
from datetime import datetime
from pathlib import Path

# Suppress OpenCV logging
cv2.setLogLevel(0)

# ==================== CONFIGURATION ====================
# Camera 1
CAMERA1_IP = "192.168.0.100"
CAMERA1_USERNAME = "admin"
CAMERA1_PASSWORD = "LBEVFF"

# Camera 2
CAMERA2_IP = "192.168.0.107"
CAMERA2_USERNAME = "admin"
CAMERA2_PASSWORD = "OCASTA"

PORT = 554
SNAPSHOT_DIR = "snapshots"
BUFFER_SIZE = 1
MAX_FRAME_WIDTH = 1280

RTSP_TEMPLATES = [
    "rtsp://{username}:{password}@{ip}:{port}/Streaming/Channels/102?tcp",  # Sub-stream
    "rtsp://{username}:{password}@{ip}:{port}/h264/ch1/sub_stream/av_stream",
    "rtsp://{username}:{password}@{ip}:{port}/ISAPI/Streaming/channels/102",
]


class CameraStream:
    """Handle single camera stream in a thread"""
    
    def __init__(self, camera_id, ip, username, password):
        self.camera_id = camera_id
        self.ip = ip
        self.username = username
        self.password = password
        self.cap = None
        self.frame = None
        self.running = False
        self.show_fps = True
        self.fps = 0
        self.lock = threading.Lock()
        
        Path(SNAPSHOT_DIR).mkdir(exist_ok=True)
    
    def get_rtsp_urls(self):
        """Generate RTSP URLs"""
        urls = []
        for template in RTSP_TEMPLATES:
            url = template.format(
                username=self.username,
                password=self.password,
                ip=self.ip,
                port=PORT
            )
            urls.append(url)
        return urls
    
    def connect(self):
        """Connect to camera"""
        urls = self.get_rtsp_urls()
        
        for i, url in enumerate(urls, 1):
            print(f"[Camera {self.camera_id}] [{i}/{len(urls)}] Trying: {url.replace(self.password, '****')}")
            
            try:
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER_SIZE)
                cap.set(cv2.CAP_PROP_FPS, 20)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        h, w = frame.shape[:2]
                        print(f"[Camera {self.camera_id}] ✓ Connected! Resolution: {w}x{h}")
                        self.cap = cap
                        return True
                    else:
                        cap.release()
                else:
                    cap.release()
            except Exception as e:
                print(f"[Camera {self.camera_id}] ✗ Failed: {str(e)}")
                continue
        
        print(f"[Camera {self.camera_id}] ✗ Connection failed")
        return False
    
    def start(self):
        """Start reading frames in thread"""
        if not self.cap:
            return False
        
        self.running = True
        thread = threading.Thread(target=self._read_frames, daemon=True)
        thread.start()
        return True
    
    def _read_frames(self):
        """Read frames continuously"""
        frame_count = 0
        start_time = time.time()
        
        while self.running:
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                # Resize if needed
                h, w = frame.shape[:2]
                if w > MAX_FRAME_WIDTH:
                    scale = MAX_FRAME_WIDTH / w
                    new_w = MAX_FRAME_WIDTH
                    new_h = int(h * scale)
                    frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                
                # Calculate FPS
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    self.fps = frame_count / elapsed
                
                # Add overlay
                frame = self._add_overlay(frame)
                
                with self.lock:
                    self.frame = frame
            else:
                time.sleep(0.01)
    
    def _add_overlay(self, frame):
        """Add status overlay"""
        h, w = frame.shape[:2]
        
        # Camera ID
        cv2.putText(frame, f"Camera {self.camera_id} - {self.ip}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # FPS
        if self.show_fps:
            cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        return frame
    
    def get_frame(self):
        """Get current frame"""
        with self.lock:
            return self.frame.copy() if self.frame is not None else None
    
    def save_snapshot(self):
        """Save snapshot"""
        frame = self.get_frame()
        if frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{SNAPSHOT_DIR}/camera{self.camera_id}_{timestamp}.jpg"
            if cv2.imwrite(filename, frame):
                print(f"[Camera {self.camera_id}] ✓ Snapshot saved: {filename}")
    
    def stop(self):
        """Stop streaming"""
        self.running = False
        if self.cap:
            self.cap.release()


def main():
    """Main entry point"""
    print("=" * 60)
    print("Dual Hikvision Camera Stream Application")
    print("=" * 60)
    print(f"Camera 1: {CAMERA1_IP}")
    print(f"Camera 2: {CAMERA2_IP}")
    print("=" * 60)
    
    # Create camera streams
    camera1 = CameraStream(1, CAMERA1_IP, CAMERA1_USERNAME, CAMERA1_PASSWORD)
    camera2 = CameraStream(2, CAMERA2_IP, CAMERA2_USERNAME, CAMERA2_PASSWORD)
    
    # Connect cameras
    print("\n[Connecting to cameras...]")
    cam1_connected = camera1.connect()
    cam2_connected = camera2.connect()
    
    if not cam1_connected and not cam2_connected:
        print("\n✗ Failed to connect to both cameras")
        sys.exit(1)
    
    # Start streaming
    if cam1_connected:
        camera1.start()
    if cam2_connected:
        camera2.start()
    
    time.sleep(1)  # Wait for frames
    
    print("\n=== STREAMING STARTED ===")
    print("Controls:")
    print("  'q' - Quit")
    print("  's' - Save snapshots")
    print("  'f' - Toggle FPS display")
    print("========================\n")
    
    # Create windows
    if cam1_connected:
        cv2.namedWindow(f"Camera 1 - {CAMERA1_IP}", cv2.WINDOW_NORMAL)
    if cam2_connected:
        cv2.namedWindow(f"Camera 2 - {CAMERA2_IP}", cv2.WINDOW_NORMAL)
    
    try:
        while True:
            # Display frames
            if cam1_connected:
                frame1 = camera1.get_frame()
                if frame1 is not None:
                    cv2.imshow(f"Camera 1 - {CAMERA1_IP}", frame1)
            
            if cam2_connected:
                frame2 = camera2.get_frame()
                if frame2 is not None:
                    cv2.imshow(f"Camera 2 - {CAMERA2_IP}", frame2)
            
            # Handle keyboard
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n[Quit requested]")
                break
            elif key == ord('s'):
                if cam1_connected:
                    camera1.save_snapshot()
                if cam2_connected:
                    camera2.save_snapshot()
            elif key == ord('f'):
                if cam1_connected:
                    camera1.show_fps = not camera1.show_fps
                if cam2_connected:
                    camera2.show_fps = not camera2.show_fps
    
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
    finally:
        # Cleanup
        camera1.stop()
        camera2.stop()
        cv2.destroyAllWindows()
        print("\n=== STREAMING STOPPED ===")
        print("Goodbye!")


if __name__ == "__main__":
    main()
