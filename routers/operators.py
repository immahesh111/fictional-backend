from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import shutil
from database import get_db
from models import Operator, LoginLog
from schemas import OperatorCreate, OperatorUpdate, OperatorResponse, LoginLogCreate, LogoutUpdate, LoginLogResponse
from auth import get_current_admin
from mqtt_client import mqtt_client
from config import settings

router = APIRouter(prefix="/api/operators", tags=["operators"])


# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)


@router.post("", response_model=OperatorResponse, status_code=status.HTTP_201_CREATED)
async def create_operator(
    name: str = Form(...),
    operator_id: str = Form(...),
    machine_no: str = Form(...),
    shift: Optional[str] = Form(None),
    face_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Create a new operator
    Optionally accepts a face image file
    Requires admin authentication
    """
    # Check if operator ID already exists
    existing_operator = db.query(Operator).filter(Operator.operator_id == operator_id).first()
    if existing_operator:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Operator with ID {operator_id} already exists"
        )
    
    # Handle face image upload
    face_image_path = None
    if face_image and face_image.filename:
        # Generate unique filename
        file_extension = os.path.splitext(face_image.filename)[1]
        filename = f"{operator_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
        file_path = os.path.join(settings.upload_dir, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(face_image.file, buffer)
        
        face_image_path = file_path
    
    # Create new operator
    new_operator = Operator(
        name=name,
        operator_id=operator_id,
        machine_no=machine_no,
        shift=shift,
        face_image_path=face_image_path
    )
    
    db.add(new_operator)
    db.commit()
    db.refresh(new_operator)
    
    return new_operator


@router.get("", response_model=List[OperatorResponse])
async def get_all_operators(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get list of all operators
    Requires admin authentication
    """
    operators = db.query(Operator).filter(Operator.deleted == False).all()
    return operators


@router.get("/{operator_id}", response_model=OperatorResponse)
async def get_operator(
    operator_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get operator details by operator ID
    Requires admin authentication
    """
    operator = db.query(Operator).filter(
        Operator.operator_id == operator_id,
        Operator.deleted == False
    ).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator with ID {operator_id} not found"
        )
    return operator


@router.put("/{operator_id}", response_model=OperatorResponse)
async def update_operator(
    operator_id: str,
    operator_data: OperatorUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Update operator information
    Requires admin authentication
    """
    operator = db.query(Operator).filter(Operator.operator_id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator with ID {operator_id} not found"
        )
    
    # Update fields
    update_data = operator_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(operator, field, value)
    
    db.commit()
    db.refresh(operator)
    
    return operator


@router.delete("/{operator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_operator(
    operator_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Delete operator by operator ID
    Also deletes associated login logs
    Requires admin authentication
    """
    operator = db.query(Operator).filter(Operator.operator_id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator with ID {operator_id} not found"
        )
    
    # Soft delete operator (mark as deleted instead of removing)
    operator.deleted = True
    operator.deleted_at = datetime.now()
    operator.synced_to_cloud = False  # Mark for sync
    
    # Soft delete associated login logs
    db.query(LoginLog).filter(LoginLog.operator_id == operator_id).update({
        "deleted": True,
        "deleted_at": datetime.now(),
        "synced_to_cloud": False
    })
    
    db.commit()
    
    return None


@router.post("/login", response_model=LoginLogResponse)
async def operator_login(
    login_data: LoginLogCreate,
    db: Session = Depends(get_db)
):
    """
    Log operator login
    Creates a login log entry and publishes MQTT unlock signal
    No authentication required (public endpoint for operator login)
    """
    # Verify operator exists
    operator = db.query(Operator).filter(Operator.operator_id == login_data.operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator with ID {login_data.operator_id} not found"
        )
    
    # Update operator status
    operator.status = "Active"
    
    # Create login log
    login_log = LoginLog(
        operator_id=login_data.operator_id,
        login_time=datetime.now(),
        shift=login_data.shift,
        date=login_data.date
    )
    
    db.add(login_log)
    db.commit()
    db.refresh(login_log)
    
    # Publish MQTT unlock signal
    timestamp = datetime.now().isoformat()
    mqtt_success = mqtt_client.publish_unlock_signal(
        operator_id=login_data.operator_id,
        machine_no=operator.machine_no
    )
    
    if not mqtt_success:
        print("Warning: Failed to publish MQTT signal")
    
    return login_log


@router.post("/logout", status_code=status.HTTP_200_OK)
async def operator_logout(
    logout_data: LogoutUpdate,
    db: Session = Depends(get_db)
):
    """
    Log operator logout
    Updates the most recent login log entry with logout time
    No authentication required
    """
    # Find operator
    operator = db.query(Operator).filter(Operator.operator_id == logout_data.operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator with ID {logout_data.operator_id} not found"
        )
    
    # Update operator status
    operator.status = "Offline"
    
    # Find most recent login log without logout time
    login_log = db.query(LoginLog).filter(
        LoginLog.operator_id == logout_data.operator_id,
        LoginLog.logout_time == None
    ).order_by(LoginLog.login_time.desc()).first()
    
    if login_log:
        login_log.logout_time = datetime.now()
        db.commit()
        
    # Publish MQTT lock signal
    mqtt_success = mqtt_client.publish_lock_signal(
        machine_no=operator.machine_no,
        operator_id=operator.operator_id
    )
    
    if not mqtt_success:
        print("Warning: Failed to publish MQTT lock signal")
    
    return {"message": "Logout successful"}
