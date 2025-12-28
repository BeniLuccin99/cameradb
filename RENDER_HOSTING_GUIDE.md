# How to Host on Render.com - Step by Step

## 📋 Prerequisites

1. GitHub account
2. Render.com account (free)
3. Your camera accessible via network

## 🚀 Deployment Steps

### Step 1: Prepare Your Code

Your code is ready! You have:
- ✅ `app.py` - Web application
- ✅ `requirements_web.txt` - Dependencies
- ✅ `render.yaml` - Render configuration
- ✅ `templates/index.html` - Web interface

### Step 2: Push to GitHub

```bash
# Initialize git repository
cd ~/Documents/OpenCv
git init

# Add files
git add app.py requirements_web.txt render.yaml templates/ Dockerfile .gitignore

# Commit
git commit -m "Add web camera streaming app"

# Create repository on GitHub (go to github.com)
# Then connect and push:
git remote add origin https://github.com/YOUR_USERNAME/camera-stream.git
git branch -M main
git push -u origin main
```

### Step 3: Sign Up on Render

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended)
4. Authorize Render to access your repositories

### Step 4: Create Web Service

1. **Click "New +"** in top right
2. **Select "Web Service"**
3. **Connect Repository**
   - Click "Connect account" if needed
   - Find your `camera-stream` repository
   - Click "Connect"

### Step 5: Configure Service

Render will auto-detect `render.yaml`, but verify:

**Basic Settings:**
- Name: `hikvision-camera-stream`
- Region: `Oregon (US West)` or closest to you
- Branch: `main`
- Runtime: `Python 3`

**Build Settings:**
- Build Command: `pip install -r requirements_web.txt`
- Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

**Plan:**
- Select `Free` (or paid for better performance)

### Step 6: Set Environment Variables

Click "Advanced" → "Add Environment Variable"

Add these variables:

| Key | Value | Notes |
|-----|-------|-------|
| `CAMERA_IP` | `192.168.0.100` | Your camera IP |
| `CAMERA_USER` | `admin` | RTSP username |
| `CAMERA_PASS` | `OCASTA` | RTSP password |
| `CAMERA_PORT` | `554` | RTSP port |
| `STREAM_TYPE` | `sub` | Use sub-stream |
| `FPS_LIMIT` | `15` | Frames per second |

**Important:** Make sure camera IP is accessible from internet!

### Step 7: Deploy

1. Click "Create Web Service"
2. Wait for deployment (3-5 minutes)
3. Watch the logs for:
   ```
   ✓ Connected! Resolution: 640x480
   Camera thread started
   ```

### Step 8: Access Your Stream

Once deployed, you'll get a URL like:
```
https://hikvision-camera-stream.onrender.com
```

Open it in your browser to see the live stream!

## 🔧 Important Notes

### Camera Network Access

⚠️ **Critical:** Your camera must be accessible from the internet!

**Option 1: Port Forwarding (Recommended)**
1. Log into your router
2. Forward port 554 to your camera IP (192.168.0.100)
3. Use your public IP in `CAMERA_IP` variable
4. Find public IP: https://whatismyipaddress.com

**Option 2: VPN/Tunnel**
1. Set up Tailscale/ZeroTier
2. Connect Render to your network
3. Use local IP

**Option 3: Cloud Camera**
If camera has cloud RTSP, use that URL directly.

### Free Tier Limitations

- ⏰ Sleeps after 15 minutes of inactivity
- 🔄 Takes 30-60 seconds to wake up
- 💾 512 MB RAM
- ⚡ Shared CPU

**To prevent sleep:**
- Upgrade to paid plan ($7/month)
- Use uptime monitoring service (UptimeRobot)

## 📊 Monitoring

### View Logs

1. Go to Render Dashboard
2. Click your service
3. Click "Logs" tab
4. Watch real-time logs

### Health Check

Visit: `https://your-app.onrender.com/health`

Should return:
```json
{
  "status": "healthy",
  "camera_connected": true,
  "camera_ip": "192.168.0.100",
  "fps": 14.8
}
```

## 🐛 Troubleshooting

### "Camera Disconnected" Message

**Check:**
1. Camera IP is correct
2. Port forwarding is set up
3. Camera is powered on
4. RTSP is enabled on camera

**Test locally first:**
```bash
python app.py
```

### Build Failed

**Check:**
- `requirements_web.txt` exists
- All files are committed to Git
- Python version is 3.11

### App Crashes

**Check logs for:**
- Connection timeout
- Memory issues
- Import errors

**Fix:**
- Increase timeout in start command
- Reduce FPS_LIMIT
- Check dependencies

### Slow Performance

**Solutions:**
1. Use `sub` stream (lower quality)
2. Reduce `FPS_LIMIT` to 10
3. Upgrade to paid plan
4. Use closer region

## 🔄 Update Deployment

When you make changes:

```bash
git add .
git commit -m "Update camera settings"
git push
```

Render auto-deploys on push!

## 💰 Cost

**Free Tier:**
- ✅ 750 hours/month
- ✅ Automatic SSL
- ✅ Custom domain support
- ⚠️ Sleeps after 15 min

**Starter Plan ($7/month):**
- ✅ Always on
- ✅ More resources
- ✅ Better performance

## 🎉 Success Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Web service created
- [ ] Environment variables set
- [ ] Camera accessible from internet
- [ ] Deployment successful
- [ ] Stream visible in browser
- [ ] Health check returns OK

## 📞 Need Help?

1. Check Render logs
2. Test locally first
3. Verify camera connectivity
4. Check GitHub repository

Your stream should now be live at:
```
https://your-app-name.onrender.com
```

Share this URL to view from anywhere! 🌍
