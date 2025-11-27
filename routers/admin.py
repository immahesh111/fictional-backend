from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Admin
from schemas import AdminCreate, AdminLogin, Token, AdminResponse
from auth import verify_password, get_password_hash, create_access_token, get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/create", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(admin_data: AdminCreate, db: Session = Depends(get_db)):
    """
    Create a new admin account
    This is a helper endpoint for initial setup
    """
    # Check if admin already exists
    existing_admin = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this username already exists"
        )
    
    # Create new admin
    hashed_password = get_password_hash(admin_data.password)
    new_admin = Admin(
        username=admin_data.username,
        hashed_password=hashed_password
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return new_admin


@router.post("/login", response_model=Token)
async def login(credentials: AdminLogin, db: Session = Depends(get_db)):
    """
    Admin login endpoint
    Returns JWT access token on successful authentication
    """
    # Find admin by username
    admin = db.query(Admin).filter(Admin.username == credentials.username).first()
    
    # Verify credentials
    if not admin or not verify_password(credentials.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": admin.username})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=AdminResponse)
async def get_current_admin_info(current_admin: Admin = Depends(get_current_admin)):
    """
    Get current admin information
    Requires authentication
    """
    return current_admin


@router.post("/reset-database", status_code=status.HTTP_200_OK)
async def reset_database(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Reset database (delete all operators and logs)
    Useful for fixing synchronization issues
    Requires admin authentication
    """
    from models import Operator, LoginLog
    
    # Delete all records
    db.query(LoginLog).delete()
    db.query(Operator).delete()
    db.commit()
    
    return {"message": "Database reset successfully"}
