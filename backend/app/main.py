from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine

# Import Models
from app.models.user import User
from app.models.investment import Investment
from app.models.platform import Platform

from app.routers.auth import auth as auth_routes
from app.routers import investments

from app.middleware.security_logger import SecutiryLoggerMiddleware
from app.middleware.alert_middleware import AlertMiddleware
from app.core.redis_client import connect_redis, close_redis
from app.core.config import settings
from app.routers import users
import uvicorn
import os

# Create all database tables if doesn't exist
def create_tables():
    Base.metadata.create_all(bind=engine)
create_tables()


app = FastAPI(
    title="AurumCap API",
    description="API RESTful for managment cripto and stocks investment portfolios in the AurumCap application",
    version="1.0.0",
    debug=settings.DEBUG
)

IS_PROD = os.getenv("IS_PROD", "false").lower() == "true"

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(users.router)
app.include_router(investments.router)

app.add_middleware(SecutiryLoggerMiddleware)
app.add_middleware(AlertMiddleware)

@app.on_event("startup")
async def on_startup():
    # Connect to redis and validate
    await connect_redis()

@app.on_event("shutdown")
async def on_shutdown():
    # Close redis connection
    await close_redis()

@app.get("/test-error")
def test_error():
    raise Exception("Test 500 error")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)