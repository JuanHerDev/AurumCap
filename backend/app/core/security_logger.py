import inspect
from fastapi import Request
from datetime import datetime
import logging

logger = logging.getLogger("security")

async def security_log_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error in {request.url.path}: {e}")

        # SOLO hacer await si la función es async
        if inspect.iscoroutinefunction(call_next):
            return await call_next(request)

        return call_next(request)
