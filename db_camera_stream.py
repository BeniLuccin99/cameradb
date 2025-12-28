#!/usr/bin/env python3
"""
Database-Driven Camera Stream Application
Select cameras from database and stream
"""

import os
import sys

os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|loglevel;quiet'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

import cv2
import threading
import time
from datetime import datetime
from pathlib import Path
from camera_manager import CameraManager

cv2.setLogLevel(0)

SNAPSHOT_DIR = "snapshots"
BUFFER_SIZE = 1
MAX_FRAME_WIDTH = 1280

RTSP_TEMPLATES = [
    "rtsp://{username}:{password}@{ip}:{port}/Streaming/Channels/102?tcp",
    "rtsp://{username}:{password}@{ip}:{port}/h264/ch1/sub_stream/av_stream",
    "rtsp://{username}:{password}@{ip}:{port}/ISAPI/Streaming/channels/102",
]


class CameraStream:
    """Handle camera stream"""
    
    def __init__(self, camera_data):
        self.camera_id = camera_data.id
        self.name = camera_data.name
        self.ip = camera_data.ip_address
        self.username = camera_data.username
        self.password = camera_data.password
        self.port = camera_data.port
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
                port=self.port
            )
            urls.append(url)
        return urls
    
    def connect(self):
        """Connect to camera"""
        urls = self.get_rtsp_urls()
        
        for i, url in enumerate(urls, 1):
            print(f"[{self.name}] [{i}/{len(urls)}] Connecting...")
            
            try:
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER_SIZE)
                cap.set(cv2.CAP_PROP_FPS, 20)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        h, w = frame.shape[:2]
                        print(f"[{self.name}] ✓ Connected! {w}x{h}")
                        self.cap = cap
                        return True
                    else:
                        cap.release()
                else:
                    cap.release()
            except Exception as e:
                print(f"[{self.name}] ✗ Failed: {str(e)}")
                continue
        
        print(f"[{self.name}] ✗ Connection failed")
        return False
    
    def start(self):
        """Start streaming thread"""
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
                h, w = frame.shape[:2]
                if w > MAX_FRAME_WIDTH:
                    scale = MAX_FRAME_WIDTH / w
                    frame = cv2.resize(frame, (MAX_FRAME_WIDTH, int(h * scale)), interpolation=cv2.INTER_AREA)
                
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    self.fps = frame_count / elapsed
                
                frame = self._add_overlay(frame)
                
                with self.lock:
                    self.frame = frame
            else:
                time.sleep(0.01)
    
    def _add_overlay(self, frame):
        """Add overlay"""
        cv2.putText(frame, f"{self.name}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
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
            filename = f"{SNAPSHOT_DIR}/{self.name.replace(' ', '_')}_{timestamp}.jpg"
            if cv2.imwrite(filename, frame):
                print(f"[{self.name}] ✓ Snapshot: {filename}")
    
    def stop(self):
        """Stop streaming"""
        self.running = False
        if self.cap:
            self.cap.release()


def select_cameras():
    """Let user select cameras to stream"""
    manager = CameraManager()
    cameras = manager.get_all_cameras()
    
    if not cameras:
        print("✗ No cameras found in database")
        print("Run: python database.py  (to initialize and seed data)")
        manager.close()
        return []
    
    print("\n=== Available Cameras ===")
    print(f"{'ID':<5} {'Name':<30} {'IP Address':<20}")
    print("-" * 55)
    
    for cam in cameras:
        print(f"{cam.id:<5} {cam.name:<30} {cam.ip_address:<20}")
    
    print("\nOptions:")
    print("  - Enter camera IDs separated by comma (e.g., 1,2)")
    print("  - Enter 'all' to stream all cameras")
    print("  - Enter 'q' to quit")
    
    choice = input("\nYour choice: ").strip().lower()
    
    if choice == 'q':
        manager.close()
        return []
    
    if choice == 'all':
        selected = cameras
    else:
        try:
            ids = [int(x.strip()) for x in choice.split(',')]
            selected = [manager.get_camera_by_id(i) for i in ids]
            selected = [c for c in selected if c is not None]
        except:
            print("✗ Invalid input")
            manager.close()
            return []
    
    manager.close()
    return selected


def main():
    """Main entry point"""
    print("=" * 60)
    print("Database-Driven Camera Stream Application")
    print("=" * 60)
    
    # Select cameras
    selected_cameras = select_cameras()
    
    if not selected_cameras:
        print("\n✗ No cameras selected")
        sys.exit(0)
    
    print(f"\n✓ Selected {len(selected_cameras)} camera(s)")
    
    # Create streams
    streams = []
    for cam_data in selected_cameras:
        stream = CameraStream(cam_data)
        if stream.connect():
            stream.start()
            streams.append(stream)
            time.sleep(0.5)
    
    if not streams:
        print("\n✗ Failed to connect to any camera")
        sys.exit(1)
    
    time.sleep(1)
    
    print("\n=== STREAMING STARTED ===")
    print("Controls:")
    print("  'q' - Quit")
    print("  's' - Save snapshots")
    print("  'f' - Toggle FPS")
    print("========================\n")
    
    # Create windows
    for stream in streams:
        cv2.namedWindow(stream.name, cv2.WINDOW_NORMAL)
    
    try:
        while True:
            for stream in streams:
                frame = stream.get_frame()
                if frame is not None:
                    cv2.imshow(stream.name, frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n[Quit requested]")
                break
            elif key == ord('s'):
                for stream in streams:
                    stream.save_snapshot()
            elif key == ord('f'):
                for stream in streams:
                    stream.show_fps = not stream.show_fps
    
    except KeyboardInterrupt:
        print("\n\n[Interrupted]")
    finally:
        for stream in streams:
            stream.stop()
        cv2.destroyAllWindows()
        print("\n=== STOPPED ===")


if __name__ == "__main__":
    main()
