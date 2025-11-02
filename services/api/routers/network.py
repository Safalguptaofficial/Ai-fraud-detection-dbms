"""
Network Graph & Fraud Map API Endpoints
Provides data for network visualization and geographic fraud analysis
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from psycopg import Connection
from deps import get_postgres
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/network", tags=["network", "visualization"])


@router.get("/graph")
async def get_network_graph(
    limit: int = Query(100, ge=1, le=1000),
    postgres: Connection = Depends(get_postgres)
):
    """
    Get network graph data for fraud ring visualization
    
    Returns nodes (accounts, merchants, IPs) and links (transactions)
    """
    try:
        cursor = postgres.cursor()
        
        # Get transactions with connections
        cursor.execute("""
            SELECT DISTINCT
                t.account_id,
                t.merchant,
                t.ip_address,
                t.device_id,
                COUNT(*) as connection_count
            FROM transactions t
            WHERE t.ip_address IS NOT NULL 
                OR t.device_id IS NOT NULL
                OR t.merchant IS NOT NULL
            GROUP BY t.account_id, t.merchant, t.ip_address, t.device_id
            ORDER BY connection_count DESC
            LIMIT %s
        """, (limit,))
        
        rows = cursor.fetchall()
        
        # Build nodes and links
        nodes = []
        links = []
        node_ids = set()
        
        for row in rows:
            account_id, merchant, ip, device, count = row
            
            # Account node
            account_node_id = f"account_{account_id}"
            if account_node_id not in node_ids:
                nodes.append({
                    "id": account_node_id,
                    "type": "account",
                    "label": f"Account {account_id}",
                    "risk": "medium"  # Would calculate from fraud score
                })
                node_ids.add(account_node_id)
            
            # Merchant node
            if merchant:
                merchant_node_id = f"merchant_{merchant}"
                if merchant_node_id not in node_ids:
                    nodes.append({
                        "id": merchant_node_id,
                        "type": "merchant",
                        "label": merchant[:30],
                        "risk": "low"
                    })
                    node_ids.add(merchant_node_id)
                
                links.append({
                    "source": account_node_id,
                    "target": merchant_node_id,
                    "type": "transaction",
                    "amount": count
                })
            
            # IP node
            if ip:
                ip_node_id = f"ip_{ip}"
                if ip_node_id not in node_ids:
                    nodes.append({
                        "id": ip_node_id,
                        "type": "ip",
                        "label": ip,
                        "risk": "medium"
                    })
                    node_ids.add(ip_node_id)
                
                links.append({
                    "source": account_node_id,
                    "target": ip_node_id,
                    "type": "shared_ip"
                })
        
        cursor.close()
        
        return {
            "nodes": nodes,
            "links": links
        }
        
    except Exception as e:
        logger.error(f"Failed to get network graph: {e}")
        # Return empty graph on error
        return {"nodes": [], "links": []}


@router.get("/map")
async def get_fraud_map(
    days: int = Query(30, ge=1, le=365),
    postgres: Connection = Depends(get_postgres)
):
    """
    Get geographic fraud data for map visualization
    
    Returns fraud locations with coordinates and statistics
    """
    try:
        cursor = postgres.cursor()
        
        # Get fraud alerts grouped by location
        cursor.execute("""
            SELECT 
                t.city,
                t.country,
                COUNT(DISTINCT a.id) as alert_count,
                COUNT(DISTINCT t.account_id) as account_count,
                SUM(t.amount) as total_amount,
                MAX(CASE WHEN a.severity = 'HIGH' THEN 1 ELSE 0 END) as has_high_severity
            FROM fraud_alerts a
            JOIN transactions t ON a.txn_id = t.id
            WHERE t.city IS NOT NULL 
                AND t.country IS NOT NULL
                AND a.created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY t.city, t.country
            HAVING COUNT(DISTINCT a.id) > 0
            ORDER BY alert_count DESC
            LIMIT 100
        """, (days,))
        
        rows = cursor.fetchall()
        
        # Map of common cities to coordinates (in production, use geocoding API)
        city_coords: dict = {
            'New York': (40.7128, -74.0060),
            'Los Angeles': (34.0522, -118.2437),
            'Chicago': (41.8781, -87.6298),
            'Houston': (29.7604, -95.3698),
            'London': (51.5074, -0.1278),
            'Paris': (48.8566, 2.3522),
            'Tokyo': (35.6762, 139.6503),
            'Lagos': (6.5244, 3.3792),
            'Mumbai': (19.0760, 72.8777),
            'Beijing': (39.9042, 116.4074),
        }
        
        locations = []
        for row in rows:
            city, country, alert_count, account_count, total_amount, has_high = row
            
            # Try to get coordinates
            lat, lon = city_coords.get(city, (None, None))
            
            # If not found, use country centroid (simplified)
            if lat is None:
                country_coords: dict = {
                    'USA': (39.8283, -98.5795),
                    'UK': (55.3781, -3.4360),
                    'FR': (46.6034, 1.8883),
                    'JP': (36.2048, 138.2529),
                    'NG': (9.0820, 8.6753),
                    'IN': (20.5937, 78.9629),
                    'CN': (35.8617, 104.1954),
                }
                lat, lon = country_coords.get(country, (0, 0))
            
            locations.append({
                "id": len(locations) + 1,
                "lat": lat or 0,
                "lon": lon or 0,
                "city": city,
                "country": country,
                "count": alert_count,
                "totalAmount": float(total_amount or 0),
                "severity": "HIGH" if has_high else "MEDIUM" if alert_count > 10 else "LOW",
                "accountCount": account_count
            })
        
        cursor.close()
        
        return {
            "locations": locations,
            "total": len(locations)
        }
        
    except Exception as e:
        logger.error(f"Failed to get fraud map data: {e}")
        return {"locations": [], "total": 0}

