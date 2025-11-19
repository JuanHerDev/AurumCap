from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import user as user_models
from app.utils.users import user as utils
from app.core.redis_client import redis_client
from app.core.config import settings
from datetime import datetime, timedelta, timezone
import os
import requests

router = APIRouter(prefix="/auth/oauth/google", tags=["OAuth Google"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")

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
        "&access_type=offline"
        "&prompt=consent"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    # 1. Exchange code for token
    token_res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )

    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange Google code")

    token_json = token_res.json()
    google_access_token = token_json.get("access_token")

    # 2. User info
    user_info = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {google_access_token}"},
    ).json()

    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    # 3. Create or fetch user
    user = db.query(user_models.User).filter(user_models.User.email == email).first()

    if not user:
        user = user_models.User(
            email=email,
            full_name=name,
            auth_provider="google",
            picture_url=picture,
            hashed_password=None,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4. Access token
    access_token = utils.create_access_token(
        subject=user.id,
        extra_data={
            "email": user.email,
            "name": user.full_name,
            "picture": user.picture_url,
        },
    )

    # 5. Refresh token
    refresh_token, expires_at = utils.create_refresh_token(subject=user.id)

    redis_client.setex(
        f"refresh:{refresh_token}",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        str(user.id),
    )

    # 6. FRONTEND REDIRECT (create here)
    redirect_url = f"{settings.FRONTEND_URL}/oauth-success?access_token={access_token}"
    response = RedirectResponse(url=redirect_url, status_code=302)

    # 7. Set cookie on this SAME response
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.IS_PROD,
        samesite="none" if settings.IS_PROD else "lax",
        path=settings.REFRESH_COOKIE_PATH,
        expires=int((expires_at - datetime.now(timezone.utc)).total_seconds()),
    )

    return response
