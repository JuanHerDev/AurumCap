from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.db.database import SessionLocal
from app.models.access_log import AccessLog
import time
import logging

class SecutiryLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        ip = request.client.host
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        path = request.url.path

        db = SessionLocal()
        response = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logging.error(f"Error in {path}: {str(e)}")

            response  = JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"}
            )

        finally:
            duration = (time.time() - start_time) * 1000  # in milliseconds

            log_entry = AccessLog(
                ip=ip,
                method=method,
                path=path,
                user_agent=user_agent,
                status_code=status_code,
                response_time_ms=duration
            )

            try:
                db.add(log_entry)
                db.commit()
            except Exception as log_err:
                logging.error(f"Failed saving log: {log_err}")
                db.rollback()
            finally:
                db.close()

            logging.info(f"{method} {path} | {status_code} | {round(duration, 2)}ms | IP {ip}")

            return response
