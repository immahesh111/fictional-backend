from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Operator, LoginLog, Admin
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel
import os
import base64
from config import settings

router = APIRouter(prefix="/api/sync", tags=["sync"])


# ============= SYNC ALL DATA =============

@router.get("/all")
async def get_all_data_since(since: str = "2000-01-01T00:00:00", db: Session = Depends(get_db)):
    """
    Get ALL data (operators, logs, admins) updated since timestamp
    Used by Pi to pull complete state from cloud
    """
    try:
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
    except ValueError:
        since_dt = datetime(2000, 1, 1)
    
    # Get operators
    operators = db.query(Operator).filter(
        Operator.created_at > since_dt
    ).all()
    
    operators_data = []
    for op in operators:
        # Encode face image to base64 if exists
        face_image_b64 = None
        if op.face_image_path and os.path.exists(op.face_image_path):
            try:
                with open(op.face_image_path, 'rb') as f:
                    face_image_b64 = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                print(f"Error encoding image: {e}")
        
        operators_data.append({
            "operator_id": op.operator_id,
            "name": op.name,
            "machine_no": op.machine_no,
            "shift": op.shift,
            "status": op.status,
            "face_image_b64": face_image_b64,
            "created_at": op.created_at.isoformat(),
            "cloud_updated_at": op.cloud_updated_at.isoformat() if op.cloud_updated_at else None,
            "deleted": op.deleted,
            "deleted_at": op.deleted_at.isoformat() if op.deleted_at else None
        })
    
    # Get login logs
    logs = db.query(LoginLog).filter(
        LoginLog.created_at > since_dt
    ).all()
    
    logs_data = []
    for log in logs:
        logs_data.append({
            "operator_id": log.operator_id,
            "login_time": log.login_time.isoformat(),
            "logout_time": log.logout_time.isoformat() if log.logout_time else None,
            "shift": log.shift,
            "date": log.date,
            "created_at": log.created_at.isoformat(),
            "deleted": log.deleted,
            "deleted_at": log.deleted_at.isoformat() if log.deleted_at else None
        })
    
    # Get admins
    admins = db.query(Admin).filter(
        Admin.created_at > since_dt
    ).all()
    
    admins_data = []
    for admin in admins:
        admins_data.append({
            "id": admin.id,
            "username": admin.username,
            "hashed_password": admin.hashed_password,
            "created_at": admin.created_at.isoformat()
        })
    
    return {
        "operators": operators_data,
        "logs": logs_data,
        "admins": admins_data,
        "sync_timestamp": datetime.now().isoformat()
    }


@router.post("/all")
async def receive_all_data(data: Dict, db: Session = Depends(get_db)):
    """
    Receive ALL data from Raspberry Pi
    Handles operators, logs, admins with timestamp-based conflict resolution
    """
    operators_count = 0
    logs_count = 0
    admins_count = 0
    
    # Sync Operators
    for op_data in data.get('operators', []):
        try:
            existing = db.query(Operator).filter(
                Operator.operator_id == op_data['operator_id']
            ).first()
            
            incoming_timestamp = datetime.fromisoformat(op_data.get('created_at', '2000-01-01T00:00:00'))
            
            if existing:
                # Latest timestamp wins
                existing_timestamp = existing.cloud_updated_at or existing.created_at
                if incoming_timestamp > existing_timestamp:
                    existing.name = op_data['name']
                    existing.machine_no = op_data['machine_no']
                    existing.shift = op_data.get('shift')
                    existing.status = op_data.get('status', 'Offline')
                    existing.deleted = op_data.get('deleted', False)
                    existing.deleted_at = datetime.fromisoformat(op_data['deleted_at']) if op_data.get('deleted_at') else None
                    existing.cloud_updated_at = datetime.now()
                    
                    # Handle face image
                    if op_data.get('face_image_b64'):
                        try:
                            image_data = base64.b64decode(op_data['face_image_b64'])
                            filename = f"{op_data['operator_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                            filepath = os.path.join(settings.upload_dir, filename)
                            with open(filepath, 'wb') as f:
                                f.write(image_data)
                            existing.face_image_path = filepath
                        except Exception as e:
                            print(f"Error saving image: {e}")
            else:
                # Create new
                face_image_path = None
                if op_data.get('face_image_b64'):
                    try:
                        image_data = base64.b64decode(op_data['face_image_b64'])
                        filename = f"{op_data['operator_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        filepath = os.path.join(settings.upload_dir, filename)
                        os.makedirs(settings.upload_dir, exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(image_data)
                        face_image_path = filepath
                    except Exception as e:
                        print(f"Error saving image: {e}")
                
                operator = Operator(
                    operator_id=op_data['operator_id'],
                    name=op_data['name'],
                    machine_no=op_data['machine_no'],
                    shift=op_data.get('shift'),
                    status=op_data.get('status', 'Offline'),
                    face_image_path=face_image_path,
                    deleted=op_data.get('deleted', False),
                    deleted_at=datetime.fromisoformat(op_data['deleted_at']) if op_data.get('deleted_at') else None,
                    synced_to_cloud=True,
                    cloud_updated_at=datetime.now()
                )
                db.add(operator)
            operators_count += 1
        except Exception as e:
            print(f"Error syncing operator: {e}")
    
    # Sync Login Logs
    for log_data in data.get('logs', []):
        try:
            existing = db.query(LoginLog).filter(
                LoginLog.operator_id == log_data['operator_id'],
                LoginLog.login_time == datetime.fromisoformat(log_data['login_time'])
            ).first()
            
            if not existing:
                log = LoginLog(
                    operator_id=log_data['operator_id'],
                    login_time=datetime.fromisoformat(log_data['login_time']),
                    logout_time=datetime.fromisoformat(log_data['logout_time']) if log_data.get('logout_time') else None,
                    shift=log_data['shift'],
                    date=log_data['date'],
                    deleted=log_data.get('deleted', False),
                    deleted_at=datetime.fromisoformat(log_data['deleted_at']) if log_data.get('deleted_at') else None,
                    synced_to_cloud=True,
                    synced_at=datetime.now()
                )
                db.add(log)
                logs_count += 1
        except Exception as e:
            print(f"Error syncing log: {e}")
    
    # Sync Admins
    for admin_data in data.get('admins', []):
        try:
            existing = db.query(Admin).filter(
                Admin.username == admin_data['username']
            ).first()
            
            if not existing:
                admin = Admin(
                    username=admin_data['username'],
                    hashed_password=admin_data['hashed_password']
                )
                db.add(admin)
                admins_count += 1
        except Exception as e:
            print(f"Error syncing admin: {e}")
    
    db.commit()
    
    return {
        "message": "Sync complete",
        "operators_synced": operators_count,
        "logs_synced": logs_count,
        "admins_synced": admins_count
    }
