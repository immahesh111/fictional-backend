from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Operator, LoginLog
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/sync", tags=["sync"])


class OperatorSyncData(BaseModel):
    operator_id: str
    name: str
    machine_no: str
    shift: str | None
    face_image_url: str | None
    updated_at: str


class LoginLogSyncData(BaseModel):
    operator_id: str
    login_time: str
    logout_time: str | None
    shift: str
    date: str


@router.get("/operators")
async def get_operators_since(since: str = "2000-01-01T00:00:00", db: Session = Depends(get_db)):
    """
    Get operators added/updated since timestamp
    Used by Raspberry Pi to pull new operators from cloud
    """
    try:
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
    except ValueError:
        since_dt = datetime(2000, 1, 1)
    
    operators = db.query(Operator).filter(
        Operator.created_at > since_dt
    ).all()
    
    result = []
    for op in operators:
        result.append({
            "operator_id": op.operator_id,
            "name": op.name,
            "machine_no": op.machine_no,
            "shift": op.shift,
            "face_image_url": f"/uploads/{op.face_image_path.split('/')[-1]}" if op.face_image_path else None,
            "updated_at": op.created_at.isoformat()
        })
    
    return result


@router.post("/logs")
async def receive_logs(logs: List[Dict], db: Session = Depends(get_db)):
    """
    Receive logs from Raspberry Pi
    Stores logs sent from local Pi database to cloud database
    """
    count = 0
    for log_data in logs:
        try:
            # Check if log already exists (avoid duplicates)
            existing = db.query(LoginLog).filter(
                LoginLog.operator_id == log_data['operator_id'],
                LoginLog.login_time == datetime.fromisoformat(log_data['login_time'])
            ).first()
            
            if existing:
                continue
            
            log = LoginLog(
                operator_id=log_data['operator_id'],
                login_time=datetime.fromisoformat(log_data['login_time']),
                logout_time=datetime.fromisoformat(log_data['logout_time']) if log_data.get('logout_time') else None,
                shift=log_data['shift'],
                date=log_data['date'],
                synced_to_cloud=True,
                synced_at=datetime.now()
            )
            db.add(log)
            count += 1
        except Exception as e:
            print(f"Error adding log: {e}")
            continue
    
    db.commit()
    return {"message": f"Received {count} logs", "total_sent": len(logs)}


@router.post("/operators")
async def receive_operators(operators: List[Dict], db: Session = Depends(get_db)):
    """
    Receive operators from Raspberry Pi
    Used when operator is created offline on Pi
    """
    count = 0
    for op_data in operators:
        try:
            # Check if operator already exists
            existing = db.query(Operator).filter(
                Operator.operator_id == op_data['operator_id']
            ).first()
            
            if existing:
                # Update existing
                existing.name = op_data.get('name', existing.name)
                existing.machine_no = op_data.get('machine_no', existing.machine_no)
                existing.shift = op_data.get('shift', existing.shift)
                existing.synced_to_cloud = True
                existing.cloud_updated_at = datetime.now()
            else:
                # Create new
                operator = Operator(
                    operator_id=op_data['operator_id'],
                    name=op_data['name'],
                    machine_no=op_data['machine_no'],
                    shift=op_data.get('shift'),
                    face_image_path=op_data.get('face_image_path'),
                    synced_to_cloud=True,
                    cloud_updated_at=datetime.now()
                )
                db.add(operator)
            count += 1
        except Exception as e:
            print(f"Error adding operator: {e}")
            continue
    
    db.commit()
    return {"message": f"Received {count} operators", "total_sent": len(operators)}
