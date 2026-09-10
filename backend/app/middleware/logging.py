import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from typing import Callable


# Configure structured logging
logger = logging.getLogger("request_logger")
logger.setLevel(logging.INFO)

# Create console handler with structured format
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# Structured log format
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware with correlation IDs."""
    
    def __init__(self, app, log_level: str = "INFO"):
        super().__init__(app)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(self.log_level)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request headers or connection."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging."""
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-ID") or self._generate_request_id()
        
        # Get request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started | {method} {path} | "
            f"request_id={request_id} | client_ip={client_ip} | "
            f"user_agent={user_agent}"
        )
        
        if query_params:
            logger.debug(f"Query params | request_id={request_id} | {query_params}")
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration = time.time() - start_time
            logger.error(
                f"Request failed | {method} {path} | "
                f"request_id={request_id} | duration={duration:.3f}s | "
                f"error={str(e)}"
            )
            raise
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        status_code = response.status_code
        log_message = (
            f"Request completed | {method} {path} | "
            f"request_id={request_id} | status_code={status_code} | "
            f"duration={duration:.3f}s"
        )
        
        # Log level based on status code
        if status_code >= 500:
            logger.error(log_message)
        elif status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """Performance logging middleware for slow requests."""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance logging."""
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected | {request.method} {request.url.path} | "
                f"duration={duration:.3f}s | threshold={self.slow_request_threshold}s"
            )
        
        return response
