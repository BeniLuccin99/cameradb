"""
Database models for camera credentials management
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Camera(Base):
    """Camera credentials model"""
    __tablename__ = 'cameras'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    ip_address = Column(String(15), nullable=False)
    username = Column(String(50), nullable=False)
    password = Column(String(100), nullable=False)
    port = Column(Integer, default=554)
    rtsp_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Camera(name='{self.name}', ip='{self.ip_address}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'username': self.username,
            'password': self.password,
            'port': self.port,
            'rtsp_url': self.rtsp_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Database configuration
DATABASE_URL = "postgresql://postgres.ibqtnoinawypjsxlvfes:1M7KCBNBiBcsqPe4@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?pgbouncer=true"
DIRECT_URL = "postgresql://postgres.ibqtnoinawypjsxlvfes:1M7KCBNBiBcsqPe4@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"

# Create engine
engine = create_engine(DIRECT_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def seed_data():
    """Seed initial camera data"""
    db = SessionLocal()
    try:
        # Check if data already exists
        existing = db.query(Camera).count()
        if existing > 0:
            print(f"⚠ Database already has {existing} cameras. Skipping seed.")
            return
        
        # Sample cameras
        cameras = [
            Camera(
                name="Camera 1 - Main Entrance",
                ip_address="192.168.0.100",
                username="admin",
                password="LBEVFF",
                port=554,
                rtsp_url="rtsp://admin:LBEVFF@192.168.0.100:554/Streaming/Channels/102",
                is_active=True
            ),
            Camera(
                name="Camera 2 - Parking Lot",
                ip_address="192.168.0.107",
                username="admin",
                password="OCASTA",
                port=554,
                rtsp_url="rtsp://admin:OCASTA@192.168.0.107:554/Streaming/Channels/102",
                is_active=True
            ),
        ]
        
        db.add_all(cameras)
        db.commit()
        print(f"✓ Seeded {len(cameras)} cameras successfully")
        
        # Display seeded data
        for cam in cameras:
            print(f"  - {cam.name} ({cam.ip_address})")
    
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("\nSeeding data...")
    seed_data()
