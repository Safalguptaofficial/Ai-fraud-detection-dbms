from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
import logging
import json

from routers import accounts, transactions, alerts, analytics, cases, health
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
http_request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

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


# Middleware for metrics and logging
@app.middleware("http")
async def metrics_middleware(request, call_next):
    method = request.method
    endpoint = request.url.path
    
    logger.info(f"Request: {method} {endpoint}")
    
    with http_request_duration.time():
        response = await call_next(request)
    
    http_requests_total.labels(method=method, endpoint=endpoint).inc()
    
    return response


# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(accounts.router, prefix="/v1", tags=["accounts"])
app.include_router(transactions.router, prefix="/v1", tags=["transactions"])
app.include_router(alerts.router, prefix="/v1", tags=["alerts"])
app.include_router(analytics.router, prefix="/v1", tags=["analytics"])
app.include_router(cases.router, prefix="/v1", tags=["cases"])


@app.get("/")
async def root():
    return {
        "service": "fraud-dbms-api",
        "version": "1.0.0",
        "environment": settings.environment
    }


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

