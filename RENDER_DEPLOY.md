# How to Host Camera API on Render - Simple Steps

## Step 1: Push Code to GitHub

```bash
cd ~/Documents/OpenCv

# Initialize git
git init

# Add files
git add api.py database.py camera_manager.py requirements_api.txt render.yaml

# Commit
git commit -m "Camera streaming API"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/camera-api.git
git branch -M main
git push -u origin main
```

## Step 2: Sign Up on Render

1. Go to https://render.com
2. Click "Get Started"
3. Sign up with GitHub

## Step 3: Create Web Service

1. Click "New +" button (top right)
2. Select "Web Service"
3. Click "Connect account" to link GitHub
4. Find your `camera-api` repository
5. Click "Connect"

## Step 4: Configure (Auto-detected)

Render will read `render.yaml` automatically:

- **Name**: camera-streaming-api
- **Build Command**: `pip install -r requirements_api.txt`
- **Start Command**: `gunicorn api:app --bind 0.0.0.0:$PORT`
- **Plan**: Free

Click "Create Web Service"

## Step 5: Wait for Deployment

- Takes 3-5 minutes
- Watch logs in real-time
- Look for: "Starting Camera Streaming API..."

## Step 6: Get Your URL

Once deployed, you'll get:
```
https://camera-streaming-api.onrender.com
```

## Step 7: Initialize Database

Run once to add default cameras:

```bash
python database.py
```

Or add via API:
```bash
curl -X POST https://camera-streaming-api.onrender.com/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Front Door",
    "ip_address": "192.168.0.100",
    "username": "admin",
    "password": "LBEVFF",
    "port": 554
  }'
```

## Step 8: Test API

Visit in browser:
- https://camera-streaming-api.onrender.com/api/health
- https://camera-streaming-api.onrender.com/api/cameras

## Step 9: Use in Next.js

```javascript
// In your Next.js app
const API_URL = 'https://camera-streaming-api.onrender.com';

// Fetch cameras
const response = await fetch(`${API_URL}/api/cameras`);
const data = await response.json();

// Display stream
<img src={`${API_URL}/api/stream/${cameraId}`} />
```

## Done! 🎉

Your API is now live and ready for Next.js!

## Troubleshooting

**Build fails?**
- Check `requirements_api.txt` exists
- Verify Python 3.11 in render.yaml

**Database error?**
- Check DATABASE_URL in render.yaml
- Verify Supabase credentials

**Camera not connecting?**
- Camera must be accessible from internet
- Set up port forwarding on router
- Use public IP in camera settings

## Free Tier Limits

- Sleeps after 15 min inactivity
- 512 MB RAM
- 750 hours/month

Upgrade to $7/month for always-on service.
