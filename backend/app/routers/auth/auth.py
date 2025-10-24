from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from jose import JWTError
from app.utils import user as utils
from app.database import get_db
from app.models import user as user_models
from app.schemas import user as user_schema
from app.core.security import get_current_token
from app.utils.oauth import verify_google_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

"""
Local Register
"""
@router.post("/register", response_model=user_schema.Token)
def register(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(user_models.User).filter(user_models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_pw = utils.hash_password(user.password)
    new_user = user_models.User(email=user.email, hashed_password=hashed_pw, auth_provider="local", is_active=True)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = utils.create_access_token(subject=new_user.email)
    return {"access_token": access_token, "token_type": "bearer"}

"""
Local Login
"""
@router.post("/login", response_model=user_schema.Token)
def login(user: user_schema.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(user_models.User).filter(user_models.User.email == user.email).first()
    if not db_user or not db_user.hashed_password or not utils.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = utils.create_access_token(subject=db_user.email)
    return {"access_token": access_token, "token_type": "bearer"}


"""
OAuth Login (Google, Apple, etc)
"""
@router.post("/oauth/{provider}", response_model=user_schema.Token)
def oauth_login(provider: str, token: str, db: Session = Depends(get_db)):
    # provider: Google or Apple
    # token: get id by the frontend

    if provider == "google":
        user_info = verify_google_token(token)
    # elif provider == "apple":
    #     user_info = verify_apple_token(token)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider")
    
    # Search or create user
    user = db.query(user_models.User).filter_by(email=user_info["email"]).first()
    if not user:
        user = user_models.User(
            email=user_info["email"],
            full_name=user_info.get("name"),
            picture_url=user_info.get("picture"),
            auth_provider=provider,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generate token
    access_token = utils.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def get_me(current_user: user_models.User = Depends(utils.get_current_user)):
    # Return current user info by jwt token
    return current_user