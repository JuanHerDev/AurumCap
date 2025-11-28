from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine

# Import Models
from app.models.user import User
from app.models.investment import Investment
from app.models.platform import Platform

# Import Routers
from app.routers.auth import auth as auth_routes
from app.routers import platforms
from app.routers import users, portfolio, stocks, debug, setup

# Import Middleware and Config
from app.middleware.security_logger import SecutiryLoggerMiddleware
from app.middleware.alert_middleware import AlertMiddleware
from app.core.redis_client import connect_redis, close_redis
from app.core.config import settings

import uvicorn
import os

# Create all database tables if they don't exist
def create_tables():
    Base.metadata.create_all(bind=engine)

create_tables()

app = FastAPI(
    title="AurumCap API",
    description="RESTful API for managing cryptocurrency and stock investment portfolios in the AurumCap application",
    version="1.0.0",
    debug=settings.DEBUG
)

IS_PROD = os.getenv("IS_PROD", "false").lower() == "true"

# CORS origins configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(users.router)
app.include_router(platforms.router)
app.include_router(portfolio.router)
app.include_router(stocks.router)
app.include_router(debug.router)
app.include_router(setup.router, prefix="/api")

# Add custom middleware
app.add_middleware(SecutiryLoggerMiddleware)
app.add_middleware(AlertMiddleware)

@app.on_event("startup")
async def on_startup():
    """Application startup event handler"""
    # Connect to Redis and validate connection
    await connect_redis()

@app.on_event("shutdown")
async def on_shutdown():
    """Application shutdown event handler"""
    # Close Redis connection
    await close_redis()

@app.get("/test-error")
def test_error():
    """Test endpoint for error handling"""
    raise Exception("Test 500 error")

@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "AurumCap Investment API is running",
        "version": "1.0.0",
        "environment": settings.ENV
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "environment": settings.ENV
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)