import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.discord_alerts import send_discord_alert

logger = logging.getLogger(__name__)

class AlertMiddleware(BaseHTTPMiddleware):
    # Middleware to send alerts for critical errors to Discord

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            duration = round((time.time() - start_time) * 1000, 2) # in milliseconds

            # Alert if response 2 seconds
            if duration > 2000:
                try:
                    await send_discord_alert(
                        title="Respuesta lenta detectada",
                        message=f"La ruta `{request.url.path}` tardó **{duration}** ms",
                        level="warning"
                    )
                except Exception as alert_err:
                    logger.error(f"Error sending slow response alert: {str(alert_err)}")

            return response
        
        except Exception as e:

            try:
                # Send alert to Discord server
                await send_discord_alert(
                    title="Error crítico en backend",
                    message=f"Ruta: `{request.url.path}`\nMétodo: `{request.method}`\nError: `{str(e)}`",
                    level="error"
                )
            except Exception as alert_err:
                logger.error(f"Error sending critical error alert: {str(alert_err)}")

            # Return a clean response 
            return Response(
                content='{"detail": "Internal server error"}',
                media_type="application/json",
                status_code=500
            )