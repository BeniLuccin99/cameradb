# Hikvision PT Network Camera Live Stream Application

Stream live video from Hikvision DS-2DE2C400IWG/W Pan-Tilt Network Camera using Python and OpenCV.

## Features

- ✅ Live RTSP video streaming with low latency
- ✅ Multiple RTSP URL fallback options
- ✅ Auto-reconnect on stream failure
- ✅ Save snapshots with timestamps
- ✅ Video recording capability
- ✅ FPS display
- ✅ Connection status indicator
- ✅ Support for main and sub streams
- ✅ Comprehensive error handling
- ✅ Keyboard controls

## Requirements

- Python 3.8 or higher
- OpenCV (cv2) library
- Network access to camera

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Verify OpenCV installation:**
```bash
python -c "import cv2; print(cv2.__version__)"
```

## Configuration

Edit the configuration section in `camera_stream.py`:

```python
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "LBEVFF"
DEFAULT_IP = "192.168.0.100"  # Change to your camera's IP
DEFAULT_PORT = 554
```

## Usage

### Basic Usage

```bash
python camera_stream.py
```

### With Command-Line Arguments

```bash
# Specify camera IP
python camera_stream.py --ip 192.168.0.100

# Use sub-stream (lower quality, less bandwidth)
python camera_stream.py --ip 192.168.0.100 --stream sub

# Custom credentials
python camera_stream.py --ip 192.168.0.100 --username admin --password LBEVFF

# Custom port
python camera_stream.py --ip 192.168.0.100 --port 554
```

### Keyboard Controls

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `s` | Save snapshot with timestamp |
| `r` | Manually reconnect to stream |
| `f` | Toggle FPS display on/off |
| `v` | Start/Stop video recording |

## Output Directories

- **Snapshots:** `snapshots/` - Saved images with timestamp
- **Recordings:** `recordings/` - Recorded video files

## RTSP URL Formats

The application automatically tries multiple RTSP URL formats:

1. `rtsp://admin:LBEVFF@192.168.0.100:554/Streaming/Channels/101`
2. `rtsp://admin:LBEVFF@192.168.0.100:554/h264/ch1/main_stream/av_stream`
3. `rtsp://admin:LBEVFF@192.168.0.100:554/ISAPI/Streaming/channels/101`

### Stream Channels

- **Main Stream (101):** High quality, higher bandwidth
- **Sub Stream (102):** Lower quality, lower bandwidth

## Troubleshooting

### Cannot Connect to Camera

1. **Verify IP address:**
```bash
ping 192.168.0.100
```

2. **Check if RTSP port is open:**
```bash
telnet 192.168.0.100 554
# or
nc -zv 192.168.0.100 554
```

3. **Test RTSP URL with VLC Media Player:**
   - Open VLC → Media → Open Network Stream
   - Enter: `rtsp://admin:LBEVFF@192.168.0.100:554/Streaming/Channels/101`

4. **Verify credentials:**
   - Log into camera web interface
   - Check username and password
   - Ensure RTSP is enabled

### Stream Drops or Freezes

- **Use sub-stream for unstable networks:**
```bash
python camera_stream.py --stream sub
```

- **Check network bandwidth:**
  - Main stream: ~2-4 Mbps
  - Sub stream: ~512 Kbps - 1 Mbps

- **Reduce latency:**
  - Application already uses minimal buffer size
  - Ensure wired connection if possible

### Poor Video Quality

- Switch to main stream:
```bash
python camera_stream.py --stream main
```

- Check camera settings via web interface:
  - Video encoding: H.264 or H.265
  - Resolution settings
  - Bitrate configuration

### RTSP Protocol Errors

If standard URLs don't work, try these alternatives:

```
rtsp://admin:LBEVFF@192.168.0.100:554/Streaming/Channels/1
rtsp://admin:LBEVFF@192.168.0.100:554/cam/realmonitor?channel=1&subtype=0
rtsp://admin:LBEVFF@192.168.0.100:554/live/ch00_0
```

### Firewall Issues

Ensure these ports are open:
- **RTSP:** 554 (TCP/UDP)
- **HTTP:** 80 (for web interface)
- **HTTPS:** 443 (for secure web interface)

## Camera Specifications

- **Model:** DS-2DE2C400IWG/W
- **Type:** Pan-Tilt Network Camera with WiFi
- **Default Port:** 554
- **Protocol:** RTSP
- **Encoding:** H.264 / H.265
- **Default Username:** admin

## Advanced Configuration

### Adjust Reconnection Settings

Edit in `camera_stream.py`:

```python
RECONNECT_DELAY = 3  # seconds between reconnect attempts
MAX_RECONNECT_ATTEMPTS = 5  # max attempts before giving up
BUFFER_SIZE = 1  # frame buffer size (lower = less latency)
```

### Change Output Directories

```python
SNAPSHOT_DIR = "snapshots"
RECORDING_DIR = "recordings"
```

## Common Issues

### "Failed to open video stream"
- Camera is offline or unreachable
- Incorrect IP address
- RTSP not enabled on camera

### "Authentication failed"
- Wrong username or password
- Account locked due to too many failed attempts

### "Connection timeout"
- Network connectivity issues
- Firewall blocking RTSP port
- Camera firmware issue

### "Stream lag or delay"
- Network bandwidth insufficient
- Switch to sub-stream
- Use wired connection instead of WiFi

## Additional Resources

- [Hikvision RTSP URL Guide](https://www.use-ip.co.uk/forum/threads/hikvision-rtsp-stream-urls.890/)
- [OpenCV VideoCapture Documentation](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html)

## License

This project is provided as-is for educational and personal use.

## Support

For issues specific to:
- **Camera hardware:** Contact Hikvision support
- **Network setup:** Check your router/network configuration
- **Application bugs:** Review error messages and logs
