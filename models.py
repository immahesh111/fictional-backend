# from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
# from sqlalchemy.sql import func
# from database import Base


# class Admin(Base):
#     """Admin user model for authentication"""
#     __tablename__ = "admins"
    
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True, nullable=False)
#     hashed_password = Column(String, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())


# class Operator(Base):
#     """Operator model for storing operator information"""
#     __tablename__ = "operators"
    
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     operator_id = Column(String, unique=True, index=True, nullable=False)
#     machine_no = Column(String, nullable=False)
#     shift = Column(String, nullable=True)  # 'Day' or 'Night'
#     status = Column(String, default="Offline")  # 'Active' or 'Offline'
#     face_image_path = Column(String, nullable=True)  # Optional reference image
#     created_at = Column(DateTime(timezone=True), server_default=func.now())


# class LoginLog(Base):
#     """Login log model for tracking operator logins/logouts"""
#     __tablename__ = "login_logs"
    
#     id = Column(Integer, primary_key=True, index=True)
#     operator_id = Column(String, ForeignKey("operators.operator_id"), nullable=False)
#     login_time = Column(DateTime(timezone=True), nullable=False)
#     logout_time = Column(DateTime(timezone=True), nullable=True)
#     shift = Column(String, nullable=False)  # 'Day' or 'Night'
#     date = Column(String, nullable=False)  # Date in YYYY-MM-DD format
#     created_at = Column(DateTime(timezone=True), server_default=func.now())


from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base


class Admin(Base):
    """Admin user model for authentication"""
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Operator(Base):
    """Operator model for storing operator information"""
    __tablename__ = "operators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    operator_id = Column(String, unique=True, index=True, nullable=False)
    machine_no = Column(String, nullable=False)
    shift = Column(String, nullable=True)  # 'Day' or 'Night'
    status = Column(String, default="Offline")  # 'Active' or 'Offline'
    face_image_path = Column(String, nullable=True)  # Optional reference image
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Sync tracking fields
    synced_to_cloud = Column(Boolean, default=False)  # Whether synced to cloud
    cloud_updated_at = Column(DateTime(timezone=True), nullable=True)  # Last cloud update


class LoginLog(Base):
    """Login log model for tracking operator logins/logouts"""
    __tablename__ = "login_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(String, ForeignKey("operators.operator_id"), nullable=False)
    login_time = Column(DateTime(timezone=True), nullable=False)
    logout_time = Column(DateTime(timezone=True), nullable=True)
    shift = Column(String, nullable=False)  # 'Day' or 'Night'
    date = Column(String, nullable=False)  # Date in YYYY-MM-DD format
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Sync tracking fields
    synced_to_cloud = Column(Boolean, default=False)  # Whether synced to cloud
    synced_at = Column(DateTime(timezone=True), nullable=True)  # When synced
