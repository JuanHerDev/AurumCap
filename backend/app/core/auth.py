# app/core/auth.py - SOLO Google OAuth utilities
import os
import httpx
from fastapi import HTTPException
from app.core.config import settings

async def exchange_google_code_for_token(code: str) -> dict:
    """
    Intercambia código de Google por tokens
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                error_detail = response.json().get("error_description", "Google OAuth failed")
                raise HTTPException(status_code=400, detail=error_detail)
                
            return response.json()
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Google OAuth service unavailable")

def build_google_oauth_url():
    """
    Genera URL para autenticación con Google
    """
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{query_string}"

async def verify_google_id_token(id_token: str) -> dict:
    """
    Verifica el ID token de Google usando su endpoint
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Google ID token")
                
            token_info = response.json()
            
            # Verificar audience
            if token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
                raise HTTPException(status_code=400, detail="Invalid token audience")
                
            return {
                "email": token_info["email"],
                "name": token_info.get("name"),
                "picture": token_info.get("picture"),
                "email_verified": token_info.get("email_verified", "false") == "true",
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Google verification service unavailable")