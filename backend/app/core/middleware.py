"""
Custom Middleware for Security, Logging, Rate Limiting, and Compression
"""
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
import gzip
import json
from typing import Callable
import asyncio
from datetime import datetime

from app.config.settings import settings
from app.core.dependencies import get_redis_client

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.redis_client = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Initialize Redis client if not done
        if not self.redis_client:
            self.redis_client = await get_redis_client()
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Different rate limits for different endpoints
        if request.url.path.startswith("/api/v1/auth/"):
            limit = settings.RATE_LIMIT_AUTH_REQUESTS
            window = settings.RATE_LIMIT_AUTH_WINDOW
            key = f"rate_limit:auth:{client_ip}"
        else:
            limit = settings.RATE_LIMIT_REQUESTS
            window = settings.RATE_LIMIT_WINDOW
            key = f"rate_limit:api:{client_ip}"
        
        # Check rate limit
        try:
            current_count = await self.redis_client.get(key)
            
            if current_count is None:
                await self.redis_client.setex(key, window, 1)
            else:
                current_count = int(current_count)
                if current_count >= limit:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "detail": f"Maximum {limit} requests per {window} seconds",
                            "retry_after": window
                        },
                        headers={"Retry-After": str(window)}
                    )
                await self.redis_client.incr(key)
        
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue without rate limiting if Redis fails
        
        response = await call_next(request)
        
        # Add rate limit headers
        try:
            remaining_requests = max(0, limit - int(await self.redis_client.get(key) or 0))
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining_requests)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)
        except:
            pass
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address handling proxies"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get client info
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} - User-Agent: {user_agent[:100]}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} "
                f"in {process_time:.4f}s for {request.method} {request.url.path}"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} in {process_time:.4f}s "
                f"for {request.method} {request.url.path}",
                exc_info=True
            )
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class CompressionMiddleware(BaseHTTPMiddleware):
    """Response compression middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Check if client accepts gzip
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response
        
        # Only compress JSON responses over 1KB
        if (
            response.headers.get("Content-Type", "").startswith("application/json") and
            hasattr(response, "body") and
            len(response.body) > 1024
        ):
            # Compress the response body
            compressed_body = gzip.compress(response.body)
            
            # Update response
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = str(len(compressed_body))
            
            # Create new response with compressed body
            return Response(
                content=compressed_body,
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type
            )
        
        return response

class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware with enhanced security"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("Origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            if origin and self.is_allowed_origin(origin):
                response = Response()
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, PUT, DELETE, PATCH, OPTIONS"
                )
                response.headers["Access-Control-Allow-Headers"] = (
                    "Authorization, Content-Type, X-Requested-With"
                )
                response.headers["Access-Control-Max-Age"] = "86400"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                return response
            else:
                return Response(status_code=403)
        
        response = await call_next(request)
        
        # Add CORS headers to actual requests
        if origin and self.is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    def is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed"""
        return origin in settings.CORS_ORIGINS

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Request validation and sanitization"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate request size
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > settings.MAX_FILE_SIZE:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": "Request too large"}
            )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("Content-Type", "")
            if not any(ct in content_type for ct in [
                "application/json",
                "multipart/form-data",
                "application/x-www-form-urlencoded"
            ]):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"error": "Unsupported media type"}
                )
        
        return await call_next(request)

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Health check middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Quick health check endpoint
        if request.url.path == "/health/quick":
            return JSONResponse(
                content={
                    "status": "healthy",
                    "timestamp": int(time.time())
                }
            )
        
        return await call_next(request)

class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Security audit logging middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.suspicious_patterns = [
            # SQL injection patterns
            r"union\s+select",
            r"drop\s+table",
            r"exec\s*\(",
            # XSS patterns
            r"<script",
            r"javascript:",
            r"onerror=",
            # Path traversal
            r"\.\./",
            r"\.\.\\",
            # Command injection
            r";\s*rm\s+",
            r";\s*cat\s+",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for suspicious patterns in URL and headers
        suspicious_activity = self.detect_suspicious_activity(request)
        
        if suspicious_activity:
            client_ip = self.get_client_ip(request)
            logger.warning(
                f"Suspicious activity detected from {client_ip}: "
                f"{suspicious_activity} - URL: {request.url}"
            )
            
            # Log to security audit
            # In production, you might want to block the request
            # or add the IP to a blacklist
        
        return await call_next(request)
    
    def detect_suspicious_activity(self, request: Request) -> str:
        """Detect suspicious patterns in request"""
        import re
        
        # Check URL path
        url_path = str(request.url).lower()
        for pattern in self.suspicious_patterns:
            if re.search(pattern, url_path, re.IGNORECASE):
                return f"Suspicious URL pattern: {pattern}"
        
        # Check headers
        for header_name, header_value in request.headers.items():
            header_value_lower = header_value.lower()
            for pattern in self.suspicious_patterns:
                if re.search(pattern, header_value_lower, re.IGNORECASE):
                    return f"Suspicious header pattern in {header_name}: {pattern}"
        
        return ""
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"

class DatabaseTransactionMiddleware(BaseHTTPMiddleware):
    """Database transaction management middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add transaction ID for tracking
        import uuid
        transaction_id = str(uuid.uuid4())
        request.state.transaction_id = transaction_id
        
        # Add to response headers for debugging
        response = await call_next(request)
        response.headers["X-Transaction-ID"] = transaction_id
        
        return response

# Custom exception handler middleware
class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """Global exception handling"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unexpected error in {request.method} {request.url.path}: {str(e)}",
                exc_info=True
            )
            
            # Return generic error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "timestamp": int(time.time())
                }
            )