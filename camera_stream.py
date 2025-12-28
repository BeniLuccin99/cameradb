#!/usr/bin/env python3
"""
Hikvision PT Network Camera Live Stream Application
Model: DS-2DE2C400IWG/W

Usage:
    python camera_stream.py
    python camera_stream.py --ip 192.168.0.100 --stream sub
    python camera_stream.py --ip 192.168.0.100 --username admin --password LBEVFF

Controls:
    'q' - Quit application
    's' - Save snapshot with timestamp
    'r' - Reconnect to stream
    'f' - Toggle FPS display
    'v' - Start/Stop video recording
"""

import os
import sys

# Suppress FFmpeg warnings BEFORE importing cv2
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|loglevel;quiet'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

import cv2
import argparse
import time
from datetime import datetime
from pathlib import Path

# Suppress OpenCV logging
cv2.setLogLevel(0)

# ==================== CONFIGURATION ====================
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "LBEVFF"
DEFAULT_IP = "192.168.0.100"
DEFAULT_PORT = 554
SNAPSHOT_DIR = "snapshots"
RECORDING_DIR = "recordings"
RECONNECT_DELAY = 3
MAX_RECONNECT_ATTEMPTS = 5
BUFFER_SIZE = 1
MAX_FRAME_WIDTH = 1280  # Resize frames larger than this

# RTSP URL templates - SUB-STREAM FIRST to avoid swscaler errors
RTSP_TEMPLATES = [
    "rtsp://{username}:{password}@{ip}:{port}/Streaming/Channels/{channel}?tcp",
    "rtsp://{username}:{password}@{ip}:{port}/h264/ch1/{stream}/av_stream",
    "rtsp://{username}:{password}@{ip}:{port}/ISAPI/Streaming/channels/{channel}",
]

STREAM_CHANNELS = {
    "main": "101",
    "sub": "102"
}


class HikvisionCamera:
    """Handle Hikvision camera RTSP stream connection and operations"""
    
    def __init__(self, ip, username, password, port=554, stream_type="main"):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.stream_type = stream_type
        self.cap = None
        self.is_recording = False
        self.video_writer = None
        self.show_fps = True
        self.fps = 0
        
        # Create output directories
        Path(SNAPSHOT_DIR).mkdir(exist_ok=True)
        Path(RECORDING_DIR).mkdir(exist_ok=True)
    
    def get_rtsp_urls(self):
        """Generate list of RTSP URLs to try"""
        channel = STREAM_CHANNELS[self.stream_type]
        urls = []
        
        for template in RTSP_TEMPLATES:
            url = template.format(
                username=self.username,
                password=self.password,
                ip=self.ip,
                port=self.port,
                channel=channel,
                stream="main_stream" if self.stream_type == "main" else "sub_stream"
            )
            urls.append(url)
        
        return urls
    
    def connect(self):
        """Attempt to connect to camera using multiple RTSP URL formats"""
        urls = self.get_rtsp_urls()
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Trying: {url.replace(self.password, '****')}")
            
            try:
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER_SIZE)
                cap.set(cv2.CAP_PROP_FPS, 20)  # Limit FPS
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        h, w = frame.shape[:2]
                        print(f"✓ Connected! Resolution: {w}x{h}")
                        self.cap = cap
                        return True
                    else:
                        cap.release()
                else:
                    cap.release()
            
            except Exception as e:
                print(f"✗ Failed: {str(e)}")
                continue
        
        print("✗ All connection attempts failed")
        return False
    
    def reconnect(self):
        """Reconnect to camera stream"""
        print("\n[Reconnecting...]")
        self.disconnect()
        time.sleep(RECONNECT_DELAY)
        return self.connect()
    
    def disconnect(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            self.is_recording = False
    
    def save_snapshot(self, frame):
        """Save current frame as snapshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SNAPSHOT_DIR}/snapshot_{timestamp}.jpg"
        
        if cv2.imwrite(filename, frame):
            print(f"✓ Snapshot saved: {filename}")
            return True
        else:
            print(f"✗ Failed to save snapshot")
            return False
    
    def toggle_recording(self, frame):
        """Start or stop video recording"""
        if not self.is_recording:
            # Start recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{RECORDING_DIR}/recording_{timestamp}.avi"
            
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            fps = self.cap.get(cv2.CAP_PROP_FPS) or 25.0
            height, width = frame.shape[:2]
            
            self.video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
            self.is_recording = True
            print(f"● Recording started: {filename}")
        else:
            # Stop recording
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            self.is_recording = False
            print("■ Recording stopped")
    
    def add_overlay(self, frame):
        """Add status overlay to frame"""
        height, width = frame.shape[:2]
        
        # Connection status
        status_text = "● LIVE"
        cv2.putText(frame, status_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # FPS display
        if self.show_fps:
            fps_text = f"FPS: {self.fps:.1f}"
            cv2.putText(frame, fps_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Recording indicator
        if self.is_recording:
            cv2.circle(frame, (width - 30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (width - 70, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Stream type
        stream_text = f"Stream: {self.stream_type.upper()}"
        cv2.putText(frame, stream_text, (10, height - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def stream(self):
        """Main streaming loop"""
        if not self.cap or not self.cap.isOpened():
            print("✗ Camera not connected. Call connect() first.")
            return
        
        print("\n=== STREAMING STARTED ===")
        print("Controls:")
        print("  'q' - Quit")
        print("  's' - Save snapshot")
        print("  'r' - Reconnect")
        print("  'f' - Toggle FPS display")
        print("  'v' - Start/Stop recording")
        print("========================\n")
        
        window_name = f"Hikvision Camera - {self.ip}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        frame_count = 0
        start_time = time.time()
        reconnect_attempts = 0
        
        while True:
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                print("✗ Stream lost. Attempting to reconnect...")
                
                if reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
                    reconnect_attempts += 1
                    if self.reconnect():
                        reconnect_attempts = 0
                        continue
                    else:
                        print(f"Reconnect attempt {reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS} failed")
                        time.sleep(RECONNECT_DELAY)
                        continue
                else:
                    print(f"✗ Max reconnect attempts reached. Exiting.")
                    break
            
            reconnect_attempts = 0
            
            # Resize large frames to avoid swscaler issues
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
            frame = self.add_overlay(frame)
            
            # Write to video file if recording
            if self.is_recording and self.video_writer:
                self.video_writer.write(frame)
            
            # Display frame
            cv2.imshow(window_name, frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n[Quit requested]")
                break
            elif key == ord('s'):
                self.save_snapshot(frame)
            elif key == ord('r'):
                print("\n[Manual reconnect requested]")
                if self.reconnect():
                    frame_count = 0
                    start_time = time.time()
            elif key == ord('f'):
                self.show_fps = not self.show_fps
            elif key == ord('v'):
                self.toggle_recording(frame)
        
        # Cleanup
        cv2.destroyAllWindows()
        self.disconnect()
        print("\n=== STREAMING STOPPED ===")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Hikvision PT Network Camera Live Stream",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--ip", default=DEFAULT_IP, 
                       help=f"Camera IP address (default: {DEFAULT_IP})")
    parser.add_argument("--username", default=DEFAULT_USERNAME,
                       help=f"Camera username (default: {DEFAULT_USERNAME})")
    parser.add_argument("--password", default=DEFAULT_PASSWORD,
                       help=f"Camera password (default: {DEFAULT_PASSWORD})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                       help=f"RTSP port (default: {DEFAULT_PORT})")
    parser.add_argument("--stream", choices=["main", "sub"], default="sub",
                       help="Stream quality: main (high) or sub (low) - DEFAULT: sub to avoid errors (default: sub)")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("Hikvision Camera Stream Application")
    print("=" * 50)
    print(f"Camera IP: {args.ip}")
    print(f"Username: {args.username}")
    print(f"Stream: {args.stream} (sub-stream recommended to avoid errors)")
    print("=" * 50)
    
    # Create camera instance
    camera = HikvisionCamera(
        ip=args.ip,
        username=args.username,
        password=args.password,
        port=args.port,
        stream_type=args.stream
    )
    
    # Connect to camera
    print("\n[Connecting to camera...]")
    if not camera.connect():
        print("\n✗ Failed to connect to camera")
        print("\nTroubleshooting:")
        print("1. Verify camera IP address is correct")
        print("2. Check username and password")
        print("3. Ensure camera is powered on and connected to network")
        print("4. Try pinging the camera: ping", args.ip)
        print("5. Verify RTSP is enabled in camera settings")
        print("6. Check firewall settings")
        sys.exit(1)
    
    # Start streaming
    try:
        camera.stream()
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    finally:
        camera.disconnect()
        print("Goodbye!")


if __name__ == "__main__":
    main()
