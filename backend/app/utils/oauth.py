from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


def verify_google_token(token: str) -> dict:
    """
    Verifies the validity of the Google token (id_token or access_token)
    and returns user information if valid.
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )
        return {
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
