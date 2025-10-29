"""
Real-time updates using Server-Sent Events (SSE)
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from psycopg import Connection
from deps import get_postgres
import asyncio
import json
from datetime import datetime
import random

router = APIRouter()


async def alert_stream():
    """Stream real-time fraud alerts to clients"""
    try:
        while True:
            # In production, this would query actual new alerts
            # For now, simulate alerts every 5-10 seconds
            await asyncio.sleep(random.randint(5, 10))
            
            # Simulate a new alert
            alert = {
                "id": random.randint(1000, 9999),
                "type": "fraud_alert",
                "severity": random.choice(["HIGH", "MEDIUM", "LOW"]),
                "title": random.choice([
                    "🚨 High-Risk Transaction Detected",
                    "⚠️ Velocity Anomaly",
                    "💳 Geographic Jump Alert",
                    "🔴 Midnight Transaction",
                    "⚡ Multiple Failed Attempts"
                ]),
                "message": random.choice([
                    f"Account #{random.randint(100, 999)} - ${random.randint(1000, 9999)} ATM withdrawal",
                    f"10 transactions in {random.randint(2, 5)} minutes",
                    "NYC to LA in 1 hour - impossible travel",
                    f"${random.randint(5000, 15000)} transaction at 2:30 AM",
                    "5 failed login attempts detected"
                ]),
                "account_id": random.randint(1, 100),
                "timestamp": datetime.now().isoformat(),
                "rule_code": random.choice(["MIDNIGHT_HIGH", "VELOCITY", "GEO_JUMP", "HIGH_AMOUNT"])
            }
            
            # Send as SSE event
            yield f"data: {json.dumps(alert)}\n\n"
            
    except asyncio.CancelledError:
        print("Client disconnected from alert stream")


@router.get("/realtime/alerts")
async def realtime_alerts():
    """
    Server-Sent Events endpoint for real-time fraud alerts
    
    Connect from frontend:
    ```javascript
    const eventSource = new EventSource('/v1/realtime/alerts');
    eventSource.onmessage = (event) => {
        const alert = JSON.parse(event.data);
        console.log('New alert:', alert);
    };
    ```
    """
    return StreamingResponse(
        alert_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


async def transaction_stream():
    """Stream real-time transactions"""
    try:
        while True:
            await asyncio.sleep(random.randint(2, 5))
            
            transaction = {
                "id": random.randint(10000, 99999),
                "type": "transaction",
                "account_id": random.randint(1, 100),
                "amount": round(random.uniform(10, 5000), 2),
                "merchant": random.choice(["Amazon", "Walmart", "Target", "ATM-CORP", "Gas Station"]),
                "status": random.choice(["APPROVED", "APPROVED", "APPROVED", "DECLINED"]),
                "risk_score": round(random.uniform(0, 100), 1),
                "timestamp": datetime.now().isoformat()
            }
            
            yield f"data: {json.dumps(transaction)}\n\n"
            
    except asyncio.CancelledError:
        print("Client disconnected from transaction stream")


@router.get("/realtime/transactions")
async def realtime_transactions():
    """Server-Sent Events endpoint for real-time transactions"""
    return StreamingResponse(
        transaction_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


async def metrics_stream():
    """Stream real-time system metrics"""
    try:
        while True:
            await asyncio.sleep(3)
            
            metrics = {
                "type": "metrics",
                "timestamp": datetime.now().isoformat(),
                "alerts_total": random.randint(50, 150),
                "alerts_high": random.randint(5, 25),
                "alerts_medium": random.randint(15, 50),
                "alerts_low": random.randint(20, 75),
                "transactions_per_min": random.randint(100, 500),
                "fraud_rate": round(random.uniform(0.5, 3.5), 2),
                "avg_risk_score": round(random.uniform(25, 45), 1)
            }
            
            yield f"data: {json.dumps(metrics)}\n\n"
            
    except asyncio.CancelledError:
        print("Client disconnected from metrics stream")


@router.get("/realtime/metrics")
async def realtime_metrics():
    """Server-Sent Events endpoint for real-time metrics"""
    return StreamingResponse(
        metrics_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

