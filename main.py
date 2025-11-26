from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

# Import database and models
from database import engine, Base
from models import Admin, Operator, LoginLog

# Import routers
from routers import admin, operators, reports

# Import MQTT client
from mqtt_client import mqtt_client

# Import config
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    print("🚀 Starting Face Detection IoT Application...")
    
    # Initialize database and create default admin
    from init_db import initialize
    initialize()
    
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    print(f"✅ Upload directory ready: {settings.upload_dir}")
    
    # Connect to MQTT broker
    mqtt_client.connect()
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Face Detection IoT Application...")
    mqtt_client.disconnect()
    print("✅ MQTT client disconnected")


# Create FastAPI application
app = FastAPI(
    title="Face Detection IoT API",
    description="Backend API for Face Recognition Access Control System with MQTT Integration",
    version="1.0.0",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    print(f"🔥 Unhandled Exception: {exc}")
    traceback.print_exc()
    
    with open("backend_crash.log", "a") as f:
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"Exception: {exc}\n")
        traceback.print_exc(file=f)
        f.write("-" * 50 + "\n")
        
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )


# Mount static files (for uploaded images)
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


# Include routers
app.include_router(admin.router)
app.include_router(operators.router)
app.include_router(reports.router)


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Face Detection IoT API is running",
        "version": "1.0.0",
        "status": "healthy",
        "mqtt_connected": mqtt_client.connected
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "mqtt": "connected" if mqtt_client.connected else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
