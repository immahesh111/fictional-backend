from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============= Admin Schemas =============
class AdminCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class AdminLogin(BaseModel):
    username: str
    password: str


class AdminResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# ============= Operator Schemas =============
class OperatorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    operator_id: str = Field(..., min_length=1, max_length=50)
    machine_no: str = Field(..., min_length=1, max_length=50)
    shift: Optional[str] = None


class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    machine_no: Optional[str] = None
    shift: Optional[str] = None
    status: Optional[str] = None


class OperatorResponse(BaseModel):
    id: int
    name: str
    operator_id: str
    machine_no: str
    shift: Optional[str]
    status: str
    face_image_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Login Log Schemas =============
class LoginLogCreate(BaseModel):
    operator_id: str
    shift: str
    date: str  # YYYY-MM-DD format


class LogoutUpdate(BaseModel):
    operator_id: str


class LoginLogResponse(BaseModel):
    id: int
    operator_id: str
    login_time: datetime
    logout_time: Optional[datetime]
    shift: str
    date: str
    
    class Config:
        from_attributes = True


# ============= Report Schemas =============
class ReportEntry(BaseModel):
    date: str
    shift: str
    login_time: str
    logout_time: Optional[str]
    duration_hours: Optional[float]


class OperatorReport(BaseModel):
    operator_id: str
    operator_name: str
    machine_no: str
    shift: Optional[str]
    total_logins: int
    total_hours: float
    average_duration: float
    entries: list[ReportEntry]


# ============= MQTT Schemas =============
class MQTTMessage(BaseModel):
    action: str
    operator_id: str
    machine_no: str
    timestamp: str
