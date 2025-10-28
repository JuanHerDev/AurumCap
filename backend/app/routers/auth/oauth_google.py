from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils import user as utils
from app.models import user as user_models
import os
import requests

router = APIRouter(prefix="/auth/google", tags=["OAuth Google"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

@router.get("/login")
def google_login():
    """
    Redirect user to sign in page of Google.
    """
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    """
    Handle Google's redirect after user login
    """
    # Intercambiar el "code" por un token de acceso
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data=token_data
    )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to obtain access token from Google: {token_response.text}"
        )

    token_json = token_response.json()
    access_token = token_json.get("access_token")

    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No access token from Google")

    # Obtener información del perfil del usuario
    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email found in Google user info"
        )

    # Verificar si ya existe el usuario
    user = db.query(user_models.User).filter(user_models.User.email == email).first()
    if not user:
        user = user_models.User(
            email=email,
            full_name=name,
            auth_provider="google",
            picture_url=picture,
            hashed_password=None,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generar tu JWT local
    jwt_token = utils.create_access_token(data={"sub": str(user.id)})

    return {"access_token": jwt_token, "token_type": "bearer", "email": email, "full_name": name, "picture": picture, "auth_provider": "google"}