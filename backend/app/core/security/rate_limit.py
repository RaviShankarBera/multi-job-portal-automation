from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, List
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting using in-memory store (use Redis in production)"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request headers or connection."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"
    
    def _clean_old_requests(self, client_ip: str, current_time: float) -> None:
        """Remove requests outside the current window."""
        cutoff_time = current_time - self.window_seconds
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff_time
        ]
    
    def _get_rate_limit_key(self, request: Request) -> str:
        """Generate rate limit key based on client IP and path."""
        client_ip = self._get_client_ip(request)
        return f"{client_ip}:{request.url.path}"
    
    def _check_rate_limit(self, key: str) -> tuple[bool, int, float]:
        """Check if rate limit is exceeded. Returns (allowed, remaining, retry_after)."""
        current_time = time.time()
        self._clean_old_requests(key, current_time)
        
        request_count = len(self.requests[key])
        
        if request_count >= self.max_requests:
            oldest_request = min(self.requests[key]) if self.requests[key] else current_time
            retry_after = oldest_request + self.window_seconds - current_time
            return False, 0, max(retry_after, 1.0)
        
        self.requests[key].append(current_time)
        remaining = self.max_requests - request_count - 1
        return True, remaining, 0.0
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        key = self._get_rate_limit_key(request)
        
        async with self._lock:
            allowed, remaining, retry_after = self._check_rate_limit(key)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                    "Retry-After": str(int(retry_after))
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time() + self.window_seconds)
        )
        
        return response


class EndpointRateLimiter:
    """Configurable rate limiter for specific endpoints."""
    
    def __init__(self):
        self.endpoint_limits: Dict[str, Dict] = {}
    
    def add_endpoint(self, path: str, max_requests: int, window_seconds: int = 60):
        """Add rate limit configuration for a specific endpoint."""
        self.endpoint_limits[path] = {
            "max_requests": max_requests,
            "window_seconds": window_seconds
        }
    
    def get_limits(self, path: str) -> Dict:
        """Get rate limit configuration for an endpoint."""
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        return {"max_requests": 100, "window_seconds": 60}
