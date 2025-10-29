from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
import logging
import time
from datetime import datetime
from typing import Dict

from routers import accounts, transactions, alerts, analytics, cases, health, auth, risk_scoring, realtime, users, ml_predictions
from config import settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
http_errors_total = Counter('http_errors_total', 'Total HTTP errors', ['method', 'endpoint', 'error_type'])
fraud_alerts_total = Counter('fraud_alerts_total', 'Total fraud alerts created', ['severity', 'rule'])

app = FastAPI(
    title="Fraud Detection API",
    description="API for AI-Powered Fraud Detection & Financial Crime",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting dictionary (simple in-memory, use Redis in production)
rate_limit_store: Dict[str, list] = {}
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX_REQUESTS = 100

def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit"""
    now = time.time()
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []
    
    # Remove old requests outside the window
    rate_limit_store[client_ip] = [
        timestamp for timestamp in rate_limit_store[client_ip]
        if now - timestamp < RATE_LIMIT_WINDOW
    ]
    
    # Check if limit exceeded
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    # Add current request
    rate_limit_store[client_ip].append(now)
    return True

# Middleware for metrics, logging, and rate limiting
@app.middleware("http")
async def middleware(request: Request, call_next):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info(f"Request: {method} {endpoint} from {client_ip}")
    
    # Rate limiting
    if not check_rate_limit(client_ip):
        error_msg = "Rate limit exceeded"
        logger.warning(f"{error_msg} for {client_ip}")
        http_errors_total.labels(method=method, endpoint=endpoint, error_type="rate_limit").inc()
        return JSONResponse(
            status_code=429,
            content={"detail": error_msg, "retry_after": RATE_LIMIT_WINDOW}
        )
    
    # Track duration
    with http_request_duration.time():
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Log successful requests
            logger.info(f"Response: {method} {endpoint} -> {status_code}")
            
            # Update metrics
            http_requests_total.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            return response
            
        except HTTPException as e:
            logger.error(f"HTTP error: {method} {endpoint} -> {e.status_code}: {e.detail}")
            http_errors_total.labels(method=method, endpoint=endpoint, error_type="http_error").inc()
            http_requests_total.labels(method=method, endpoint=endpoint, status=str(e.status_code)).inc()
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error: {method} {endpoint} -> {str(e)}", exc_info=True)
            http_errors_total.labels(method=method, endpoint=endpoint, error_type="internal_error").inc()
            http_requests_total.labels(method=method, endpoint=endpoint, status="500").inc()
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "timestamp": datetime.utcnow().isoformat()}
            )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.utcnow().isoformat()}
    )

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/v1/auth", tags=["authentication"])
app.include_router(accounts.router, prefix="/v1", tags=["accounts"])
app.include_router(transactions.router, prefix="/v1", tags=["transactions"])
app.include_router(alerts.router, prefix="/v1", tags=["alerts"])
app.include_router(analytics.router, prefix="/v1", tags=["analytics"])
app.include_router(cases.router, prefix="/v1", tags=["cases"])
app.include_router(risk_scoring.router, prefix="/v1", tags=["risk-scoring"])
app.include_router(realtime.router, prefix="/v1", tags=["realtime"])
app.include_router(users.router, prefix="/v1", tags=["users"])
app.include_router(ml_predictions.router, prefix="/v1", tags=["ml-predictions"])

@app.get("/")
async def root():
    return {
        "service": "fraud-dbms-api",
        "version": "1.0.0",
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)