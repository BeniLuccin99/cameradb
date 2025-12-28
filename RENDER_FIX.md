# Render Deployment Guide - Camera Streaming API

## ✅ Files Ready

All files are now ready for deployment:
- `api.py` - Flask application
- `requirements.txt` - All dependencies including gunicorn
- `templates/index.html` - Web interface

## 🚀 Deploy to Render

### Step 1: Push to GitHub

```bash
cd ~/Documents/OpenCv

git add api.py requirements.txt templates/
git commit -m "Fix gunicorn deployment"
git push
```

### Step 2: Configure Render

Go to your Render dashboard and set:

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
gunicorn api:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

**Environment Variables:**
```
CAMERA_IP=192.168.0.100
CAMERA_USER=admin
CAMERA_PASS=OCASTA
CAMERA_PORT=554
STREAM_TYPE=sub
FPS_LIMIT=15
SECRET_KEY=your-random-secret-key
```

**Health Check Path:**
```
/health
```

### Step 3: Deploy

Click "Manual Deploy" → "Deploy latest commit"

### Expected Output

```
==> Installing dependencies...
Collecting Flask==3.0.0
Collecting gunicorn==21.2.0
Collecting opencv-python-headless==4.8.1.78
Successfully installed Flask-3.0.0 gunicorn-21.2.0 opencv-python-headless-4.8.1.78 ...
==> Build successful ✓

==> Starting service...
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:10000
[INFO] Using worker: sync
[INFO] Booting worker with pid: 23
[INFO] Starting Camera Streaming API...
[INFO] Camera connected! Resolution: 640x480
[INFO] Camera stream thread started

==> Your service is live at https://your-app.onrender.com 🎉
```

## 🔍 Verify Deployment

1. **Health Check:**
   ```
   https://your-app.onrender.com/health
   ```
   Should return:
   ```json
   {
     "status": "healthy",
     "camera_connected": true,
     "camera_ip": "192.168.0.100",
     "fps": 14.8
   }
   ```

2. **View Stream:**
   ```
   https://your-app.onrender.com/
   ```

3. **API Status:**
   ```
   https://your-app.onrender.com/api/status
   ```

## 🐛 Troubleshooting

### "gunicorn: command not found"
✅ FIXED - gunicorn is now in requirements.txt

### "No module named 'cv2'"
✅ FIXED - opencv-python-headless is in requirements.txt

### "Camera not connecting"
- Ensure camera IP is accessible from internet
- Set up port forwarding on router (port 554)
- Use public IP in CAMERA_IP environment variable

### "Build succeeds but app crashes"
- Check logs for errors
- Verify all environment variables are set
- Ensure PORT is not hardcoded (Render sets it automatically)

## 📊 Monitoring

Check logs in Render dashboard:
- Build logs: Shows dependency installation
- Deploy logs: Shows app startup
- Runtime logs: Shows camera connection status

## 🎯 Success Checklist

- [x] gunicorn in requirements.txt
- [x] opencv-python-headless (not opencv-python)
- [x] Flask app named `app` in api.py
- [x] Health check at /health
- [x] PORT from environment variable
- [x] No GUI dependencies
- [x] RTSP streaming works
- [x] Error handling included

## 🌐 Your URLs

After deployment:
- **Main Page:** https://your-app.onrender.com/
- **Video Feed:** https://your-app.onrender.com/video_feed
- **Health Check:** https://your-app.onrender.com/health
- **API Status:** https://your-app.onrender.com/api/status

## 💡 Next Steps

1. Test the health endpoint
2. View the camera stream
3. Use the video feed URL in your Next.js app:
   ```javascript
   <img src="https://your-app.onrender.com/video_feed" />
   ```

Your deployment should now work perfectly! 🎉
