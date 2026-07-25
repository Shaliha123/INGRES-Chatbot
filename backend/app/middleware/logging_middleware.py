import time
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from backend.app.database import db

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        now = datetime.now(timezone.utc).isoformat()
        
        response = None
        error_msg = ""
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            error_msg = str(exc)
            raise exc
        finally:
            processing_time_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log asynchronously to MongoDB Atlas if connection active
            if db.db is not None and not request.url.path.startswith("/docs") and not request.url.path.startswith("/openapi"):
                try:
                    log_entry = {
                        "user_id": request.headers.get("x-user-id", "anonymous"),
                        "endpoint": request.url.path,
                        "method": request.method,
                        "timestamp": now,
                        "status": status_code,
                        "processing_time_ms": processing_time_ms,
                        "error_message": error_msg
                    }
                    await db.db.logs.insert_one(log_entry)
                except Exception:
                    pass
                    
        return response
