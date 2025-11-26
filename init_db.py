"""
Database initialization script
Creates tables and default admin user on first run
"""
import sys
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from models import Admin
from auth import get_password_hash
from config import settings


def init_database():
    """Initialize database tables"""
    print("🔧 Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def create_default_admin(db: Session):
    """Create default admin user if none exists"""
    # Check if any admin exists
    admin_count = db.query(Admin).count()
    
    if admin_count == 0:
        print("👤 No admin found. Creating default admin...")
        
        # Get credentials from environment or use defaults
        default_username = getattr(settings, 'default_admin_username', 'admin')
        default_password = getattr(settings, 'default_admin_password', 'admin123')
        
        # Create admin
        hashed_password = get_password_hash(default_password)
        admin = Admin(
            username=default_username,
            hashed_password=hashed_password
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"✅ Default admin created:")
        print(f"   Username: {default_username}")
        print(f"   Password: {default_password}")
        print(f"   ⚠️  Please change the default password in production!")
        
        return admin
    else:
        print(f"✅ Found {admin_count} admin(s) in database")
        return None


def initialize():
    """Main initialization function"""
    print("\n" + "="*50)
    print("Face Detection IoT - Database Initialization")
    print("="*50 + "\n")
    
    # Create tables
    init_database()
    
    # Create default admin
    db = SessionLocal()
    try:
        create_default_admin(db)
    finally:
        db.close()
    
    print("\n" + "="*50)
    print("Initialization Complete!")
    print("="*50 + "\n")


if __name__ == "__main__":
    initialize()
