"""
Camera credentials manager - CRUD operations
"""
from database import Camera, SessionLocal


class CameraManager:
    """Manage camera credentials in database"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def get_all_cameras(self, active_only=True):
        """Get all cameras"""
        query = self.db.query(Camera)
        if active_only:
            query = query.filter(Camera.is_active == True)
        return query.all()
    
    def get_camera_by_id(self, camera_id):
        """Get camera by ID"""
        return self.db.query(Camera).filter(Camera.id == camera_id).first()
    
    def get_camera_by_name(self, name):
        """Get camera by name"""
        return self.db.query(Camera).filter(Camera.name == name).first()
    
    def add_camera(self, name, ip_address, username, password, port=554, rtsp_url=None):
        """Add new camera"""
        try:
            camera = Camera(
                name=name,
                ip_address=ip_address,
                username=username,
                password=password,
                port=port,
                rtsp_url=rtsp_url,
                is_active=True
            )
            self.db.add(camera)
            self.db.commit()
            self.db.refresh(camera)
            return camera
        except Exception as e:
            self.db.rollback()
            raise e
    
    def update_camera(self, camera_id, **kwargs):
        """Update camera credentials"""
        try:
            camera = self.get_camera_by_id(camera_id)
            if not camera:
                return None
            
            for key, value in kwargs.items():
                if hasattr(camera, key):
                    setattr(camera, key, value)
            
            self.db.commit()
            self.db.refresh(camera)
            return camera
        except Exception as e:
            self.db.rollback()
            raise e
    
    def delete_camera(self, camera_id):
        """Delete camera (soft delete - set inactive)"""
        try:
            camera = self.get_camera_by_id(camera_id)
            if camera:
                camera.is_active = False
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            raise e
    
    def close(self):
        """Close database session"""
        self.db.close()


def list_cameras():
    """List all cameras"""
    manager = CameraManager()
    cameras = manager.get_all_cameras()
    
    if not cameras:
        print("No cameras found in database")
        return []
    
    print(f"\n{'ID':<5} {'Name':<30} {'IP Address':<20} {'Username':<15}")
    print("-" * 70)
    
    for cam in cameras:
        print(f"{cam.id:<5} {cam.name:<30} {cam.ip_address:<20} {cam.username:<15}")
    
    manager.close()
    return cameras


if __name__ == "__main__":
    print("=== Camera Credentials Manager ===\n")
    list_cameras()
