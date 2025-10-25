from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.database import Base, engine
from app.routers.auth import auth as auth_routes
from app.routers.auth import oauth_google as oauth_google_routes
from app.routers import users
import uvicorn

# Create all database tables if doesn't exist
def create_tables():
    Base.metadata.create_all(bind=engine)
create_tables()


app = FastAPI(
    title="AurumCap API",
    description="API RESTful for managment cripto and stocks investment portfolios in the AurumCap application",
    version="1.0.0"
)

origins = [
    "http://localhost:3000", # local frontend
    "https://aurumcap.vercel.app" # production vercell
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(oauth_google_routes.router)
app.include_router(users.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)