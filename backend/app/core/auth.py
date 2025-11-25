# app/core/auth.py - SOLO Google OAuth utilities
import os
import httpx
from fastapi import HTTPException, logger
from app.core.config import settings

async def exchange_google_code_for_token(code: str) -> dict:
    """
    Intercambia código de Google por tokens
    """
    try:
        logger.info(f"🔄 Intercambiendo código por token de Google...")
        logger.info(f"🔧 Código recibido: {code[:50]}...")
        
        # Verificar que el código no esté vacío
        if not code or code == "undefined":
            logger.error("❌ Código de Google vacío o undefined")
            raise HTTPException(status_code=400, detail="Invalid authorization code")

        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        }

        logger.info(f"🔧 Enviando solicitud a Google OAuth...")
        logger.info(f"🔧 Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
        logger.info(f"🔧 Client ID: {settings.GOOGLE_CLIENT_ID[:25]}...")
        
        async with httpx.AsyncClient() as client:
            # Aumentar timeout y agregar headers
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data=data,
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"📡 Respuesta de Google - Status: {response.status_code}")
            logger.info(f"📡 Headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                error_response = response.text
                logger.error(f"❌ Error de Google - Status: {response.status_code}")
                logger.error(f"❌ Respuesta: {error_response}")
                
                # Intentar parsear el error
                try:
                    error_json = response.json()
                    error_msg = error_json.get("error_description", error_json.get("error", "Unknown error"))
                except:
                    error_msg = error_response
                
                raise HTTPException(status_code=400, detail=f"Google OAuth error: {error_msg}")
            
            # Éxito
            token_data = response.json()
            logger.info(f"✅ Token exchange successful")
            logger.info(f"✅ Token type: {token_data.get('token_type')}")
            logger.info(f"✅ Access token: {token_data.get('access_token', '')[:20]}...")
            logger.info(f"✅ ID token: {token_data.get('id_token', '')[:20]}...")
            
            return token_data
            
    except httpx.TimeoutException:
        logger.error("⏰ Timeout en conexión con Google OAuth")
        raise HTTPException(status_code=503, detail="Google OAuth service timeout")
    except httpx.RequestError as e:
        logger.error(f"🌐 Error de conexión con Google: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Google OAuth service unavailable: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error inesperado en Google OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth authentication failed: {str(e)}")
    
    
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