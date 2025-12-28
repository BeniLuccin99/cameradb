# Next.js Integration Guide

## 🚀 Backend API (Python Flask)

Your Python backend is now a REST API that Next.js can consume.

### Deploy Backend to Render

1. **Push to GitHub**
```bash
git add .
git commit -m "Camera streaming API"
git push
```

2. **Deploy on Render**
- Go to render.com
- Connect repository
- It will auto-deploy using `render.yaml`
- Your API will be at: `https://camera-streaming-api.onrender.com`

3. **Initialize Database**
```bash
# Run once to seed cameras
python database.py
```

## 📡 API Endpoints

Base URL: `https://your-api.onrender.com`

### GET /api/cameras
Get all cameras
```json
{
  "cameras": [
    {
      "id": 1,
      "name": "Camera 1 - Main Entrance",
      "ip_address": "192.168.0.100",
      "username": "admin",
      "port": 554,
      "is_active": true,
      "stream_url": "/api/stream/1",
      "is_connected": true,
      "fps": 14.8
    }
  ],
  "count": 2
}
```

### GET /api/cameras/:id
Get single camera

### POST /api/cameras
Add new camera
```json
{
  "name": "Front Door",
  "ip_address": "192.168.0.100",
  "username": "admin",
  "password": "LBEVFF",
  "port": 554
}
```

### DELETE /api/cameras/:id
Delete camera

### GET /api/stream/:id
MJPEG video stream (use in `<img>` tag)

### GET /api/health
Health check

## 🎨 Next.js Frontend

### 1. Create Next.js App

```bash
npx create-next-app@latest camera-viewer
cd camera-viewer
```

### 2. Install Dependencies

```bash
npm install axios
```

### 3. Create API Client

**lib/api.js**
```javascript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://camera-streaming-api.onrender.com';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getCameras = async () => {
  const response = await api.get('/api/cameras');
  return response.data;
};

export const getCamera = async (id) => {
  const response = await api.get(`/api/cameras/${id}`);
  return response.data;
};

export const addCamera = async (data) => {
  const response = await api.post('/api/cameras', data);
  return response.data;
};

export const deleteCamera = async (id) => {
  const response = await api.delete(`/api/cameras/${id}`);
  return response.data;
};

export const getStreamUrl = (id) => {
  return `${API_BASE_URL}/api/stream/${id}`;
};
```

### 4. Create Camera Grid Component

**components/CameraGrid.jsx**
```javascript
'use client';
import { useState, useEffect } from 'react';
import { getCameras, getStreamUrl, deleteCamera } from '@/lib/api';

export default function CameraGrid() {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCameras();
  }, []);

  const loadCameras = async () => {
    try {
      const data = await getCameras();
      setCameras(data.cameras);
    } catch (error) {
      console.error('Failed to load cameras:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (confirm('Delete this camera?')) {
      try {
        await deleteCamera(id);
        loadCameras();
      } catch (error) {
        console.error('Failed to delete:', error);
      }
    }
  };

  if (loading) return <div>Loading cameras...</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
      {cameras.map((camera) => (
        <div key={camera.id} className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="bg-gray-800 text-white p-4 flex justify-between items-center">
            <h3 className="font-bold">{camera.name}</h3>
            <button
              onClick={() => handleDelete(camera.id)}
              className="bg-red-500 px-3 py-1 rounded text-sm hover:bg-red-600"
            >
              Delete
            </button>
          </div>
          <img
            src={getStreamUrl(camera.id)}
            alt={camera.name}
            className="w-full h-auto"
          />
          <div className="p-4 bg-gray-100">
            <p className="text-sm">📍 {camera.ip_address}</p>
            <p className="text-sm">
              {camera.is_connected ? '🟢 Connected' : '🔴 Disconnected'}
            </p>
            <p className="text-sm">FPS: {camera.fps}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### 5. Create Add Camera Form

**components/AddCameraForm.jsx**
```javascript
'use client';
import { useState } from 'react';
import { addCamera } from '@/lib/api';

export default function AddCameraForm({ onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    ip_address: '',
    username: 'admin',
    password: '',
    port: 554,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await addCamera(formData);
      onSuccess();
      setFormData({ name: '', ip_address: '', username: 'admin', password: '', port: 554 });
    } catch (error) {
      console.error('Failed to add camera:', error);
      alert('Failed to add camera');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-lg max-w-md">
      <h2 className="text-2xl font-bold mb-4">Add Camera</h2>
      
      <input
        type="text"
        placeholder="Camera Name"
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        className="w-full p-2 border rounded mb-3"
        required
      />
      
      <input
        type="text"
        placeholder="IP Address"
        value={formData.ip_address}
        onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
        className="w-full p-2 border rounded mb-3"
        required
      />
      
      <input
        type="text"
        placeholder="Username"
        value={formData.username}
        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
        className="w-full p-2 border rounded mb-3"
        required
      />
      
      <input
        type="password"
        placeholder="Password"
        value={formData.password}
        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
        className="w-full p-2 border rounded mb-3"
        required
      />
      
      <input
        type="number"
        placeholder="Port"
        value={formData.port}
        onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
        className="w-full p-2 border rounded mb-3"
      />
      
      <button
        type="submit"
        className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
      >
        Add Camera
      </button>
    </form>
  );
}
```

### 6. Main Page

**app/page.jsx**
```javascript
'use client';
import { useState } from 'react';
import CameraGrid from '@/components/CameraGrid';
import AddCameraForm from '@/components/AddCameraForm';

export default function Home() {
  const [showAddForm, setShowAddForm] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCameraAdded = () => {
    setShowAddForm(false);
    setRefreshKey(prev => prev + 1);
  };

  return (
    <main className="min-h-screen bg-gray-100">
      <header className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6">
        <h1 className="text-4xl font-bold text-center">Camera Monitoring System</h1>
      </header>
      
      <div className="p-6">
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-green-500 text-white px-6 py-3 rounded-lg mb-6 hover:bg-green-600"
        >
          {showAddForm ? 'Cancel' : '➕ Add Camera'}
        </button>
        
        {showAddForm && <AddCameraForm onSuccess={handleCameraAdded} />}
        
        <CameraGrid key={refreshKey} />
      </div>
    </main>
  );
}
```

### 7. Environment Variables

**.env.local**
```
NEXT_PUBLIC_API_URL=https://camera-streaming-api.onrender.com
```

### 8. Run Next.js App

```bash
npm run dev
```

Visit: http://localhost:3000

## 🌐 Deploy Next.js to Vercel

```bash
npm install -g vercel
vercel
```

## ✅ Complete Flow

1. **Backend (Python)** → Render.com
   - Handles RTSP connections
   - Streams MJPEG video
   - Manages database

2. **Frontend (Next.js)** → Vercel
   - Fetches camera list from API
   - Displays video streams
   - Manages cameras

3. **Database** → Supabase
   - Stores camera credentials

## 🔗 URLs

- Backend API: `https://camera-streaming-api.onrender.com`
- Frontend: `https://your-app.vercel.app`
- Stream: `https://camera-streaming-api.onrender.com/api/stream/1`

Your Next.js app is now ready! 🎉
