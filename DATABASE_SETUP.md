# Database Setup Guide

## Overview

This application uses SQLAlchemy with Supabase PostgreSQL to store camera credentials, allowing you to manage multiple cameras without hardcoding credentials.

## Features

- ✅ Store camera credentials in Supabase database
- ✅ Select cameras from database to stream
- ✅ Add/Update/Delete camera configurations
- ✅ Seed sample data for testing
- ✅ Multi-camera streaming support

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Initialize database and seed data:**
```bash
python database.py
```

This will:
- Create the `cameras` table in Supabase
- Seed 2 sample cameras

## Database Schema

### `cameras` Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key (auto-increment) |
| name | String(100) | Camera name (unique) |
| ip_address | String(15) | Camera IP address |
| username | String(50) | RTSP username |
| password | String(100) | RTSP password |
| port | Integer | RTSP port (default: 554) |
| rtsp_url | String(255) | Full RTSP URL (optional) |
| is_active | Boolean | Active status |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

## Usage

### 1. Stream Cameras from Database

```bash
python db_camera_stream.py
```

You'll be prompted to select cameras:
- Enter camera IDs: `1,2` (stream cameras 1 and 2)
- Enter `all` to stream all cameras
- Enter `q` to quit

### 2. List All Cameras

```bash
python camera_manager.py
```

### 3. Manage Cameras (Python)

```python
from camera_manager import CameraManager

manager = CameraManager()

# Get all cameras
cameras = manager.get_all_cameras()

# Get camera by ID
camera = manager.get_camera_by_id(1)

# Add new camera
new_camera = manager.add_camera(
    name="Camera 3 - Backyard",
    ip_address="192.168.0.108",
    username="admin",
    password="password123",
    port=554
)

# Update camera
manager.update_camera(1, password="new_password")

# Delete camera (soft delete)
manager.delete_camera(1)

manager.close()
```

## Sample Seeded Data

After running `python database.py`, you'll have:

| ID | Name | IP Address | Username | Password |
|----|------|------------|----------|----------|
| 1 | Camera 1 - Main Entrance | 192.168.0.100 | admin | LBEVFF |
| 2 | Camera 2 - Parking Lot | 192.168.0.107 | admin | OCASTA |

## Database Connection

The application uses two connection strings:

1. **DATABASE_URL** (Pooled): For application queries
   ```
   postgresql://postgres.ibqtnoinawypjsxlvfes:1M7KCBNBiBcsqPe4@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?pgbouncer=true
   ```

2. **DIRECT_URL**: For migrations and table creation
   ```
   postgresql://postgres.ibqtnoinawypjsxlvfes:1M7KCBNBiBcsqPe4@aws-1-eu-west-1.pooler.supabase.com:5432/postgres
   ```

## Files

- `database.py` - Database models and initialization
- `camera_manager.py` - CRUD operations for cameras
- `db_camera_stream.py` - Stream cameras from database
- `camera_stream.py` - Original single camera stream (still works)
- `dual_camera_stream.py` - Hardcoded dual camera stream

## Troubleshooting

### Connection Error

If you get connection errors:
1. Check Supabase project is active
2. Verify database password is correct
3. Ensure your IP is allowed in Supabase settings

### Table Already Exists

If you see "table already exists" error, the database is already initialized. You can:
- Skip initialization
- Drop the table manually in Supabase SQL Editor:
  ```sql
  DROP TABLE cameras;
  ```

### No Cameras Found

Run the seed script:
```bash
python database.py
```

## Security Notes

⚠️ **Important**: 
- Never commit database credentials to Git
- Use environment variables in production
- The `.env.example` file is for reference only
- Rotate passwords regularly

## Next Steps

1. Add more cameras via Python script or Supabase dashboard
2. Create a web interface for camera management
3. Add camera groups/locations
4. Implement user authentication
5. Add camera health monitoring
