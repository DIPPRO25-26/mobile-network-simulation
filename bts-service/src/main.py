"""
BTS Service - Base Transceiver Station Simulation

MVP Implementation using FastAPI and Redis

TODO for team:
- Implement HMAC signing for requests to Central
- Add handover logic based on distance/signal strength
- Implement local analytics (speed calculation, transition count)
- Add proper error handling and retry logic
- Implement health checks
- Add metrics/monitoring
- Optimize Redis caching strategy
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional
import httpx
import redis
import json
import os
from datetime import datetime
import logging
from .broadcaster import Broadcaster

# Configuration from environment variables
BTS_ID = os.getenv("BTS_ID", "BTS001")
BTS_LAC = os.getenv("BTS_LAC", "1001")
BTS_LOCATION_X = float(os.getenv("BTS_LOCATION_X", "100"))
BTS_LOCATION_Y = float(os.getenv("BTS_LOCATION_Y", "100"))
CENTRAL_API_URL = os.getenv("CENTRAL_API_URL", "http://localhost:8080")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
MCC = os.getenv("MCC", "219")  # Croatia
MNC = os.getenv("MNC", "01")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title=f"BTS Service - {BTS_ID}")

# Initialize Broadcaster
broadcaster = Broadcaster()

@app.on_event("startup")
def startup_event():
    """Start background tasks on application startup"""
    logger.info(f"Starting BTS Service {BTS_ID}")

    # Start broadcaster thread
    broadcaster.start()
    logger.info("Broadcaster started")

@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on shutdown"""
    logger.info(f"Shutting down BTS Service {BTS_ID}")
    broadcaster.stop()

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Models
class UserLocation(BaseModel):
    x: float
    y: float

class ConnectRequest(BaseModel):
    imei: str = Field(..., min_length=15, max_length=15, description="IMEI number")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    user_location: UserLocation

class ConnectResponse(BaseModel):
    status: str
    data: dict

# Helper functions
def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance between two points"""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

def should_handover(user_location: UserLocation) -> tuple[bool, Optional[str]]:
    """
    Determine if handover is needed
    
    TODO for team:
    - Implement more sophisticated handover logic
    - Consider signal strength simulation
    - Check BTS load/capacity
    - Query neighbor BTS locations from registry
    """
    distance = calculate_distance(
        BTS_LOCATION_X, BTS_LOCATION_Y,
        user_location.x, user_location.y
    )
    
    # Simple distance-based handover (threshold: 150 units)
    MAX_DISTANCE = 150.0
    if distance > MAX_DISTANCE:
        # TODO: Find nearest BTS instead of hardcoding
        return True, None  # Return None for now, implement BTS discovery
    
    return False, None

def cache_user_activity(imei: str, data: dict):
    """
    Cache user activity in Redis
    
    TODO for team:
    - Implement TTL strategy
    - Add bulk operations for performance
    - Implement cache invalidation logic
    """
    key = f"bts:{BTS_ID}:user:{imei}"
    redis_client.setex(key, 300, json.dumps(data))  # 5 min TTL

def get_cached_user(imei: str) -> Optional[dict]:
    """Get cached user data"""
    key = f"bts:{BTS_ID}:user:{imei}"
    data = redis_client.get(key)
    return json.loads(data) if data else None

async def send_to_central(data: dict) -> dict:
    """
    Send user event to Central Backend
    
    TODO for team:
    - Add HMAC signing (X-HMAC-Signature header)
    - Add timestamp header (X-Timestamp)
    - Implement retry logic with exponential backoff
    - Add circuit breaker pattern
    - Handle timeouts properly
    """
    url = f"{CENTRAL_API_URL}/api/v1/user"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to send data to Central: {e}")
            raise HTTPException(status_code=502, detail="Central Backend unreachable")

# Endpoints
@app.post("/api/v1/connect", response_model=ConnectResponse)
async def connect_user(request: ConnectRequest):
    """
    Handle user connection to BTS
    
    MVP Implementation:
    1. Receive user data from simulator
    2. Cache user activity in Redis
    3. Send data to Central Backend
    4. Return response (with handover suggestion if needed)
    
    TODO for team:
    - Validate IMEI format
    - Implement rate limiting per IMEI
    - Add local anomaly detection
    - Calculate user speed locally
    """
    logger.info(f"User {request.imei} connecting to {BTS_ID}")
    
    # Check for handover need
    needs_handover, target_bts = should_handover(request.user_location)
    
    # Prepare data for Central Backend
    central_data = {
        "imei": request.imei,
        "mcc": MCC,
        "mnc": MNC,
        "lac": BTS_LAC,
        "btsId": BTS_ID,
        "timestamp": datetime.now().isoformat(),
        "userLocation": {
            "x": request.user_location.x,
            "y": request.user_location.y
        }
    }
    
    # Send to Central Backend
    central_response = await send_to_central(central_data)
    
    # Cache user activity
    cache_data = {
        "last_seen": datetime.now().isoformat(),
        "location": {"x": request.user_location.x, "y": request.user_location.y},
        "bts_id": BTS_ID
    }
    cache_user_activity(request.imei, cache_data)
    
    # Build response
    response_data = {
        "bts_id": BTS_ID,
        "action": "handover" if needs_handover else None,
        "target_bts_id": target_bts if needs_handover else None,
        "message": "Connected successfully"
    }
    
    if needs_handover:
        logger.warning(f"Handover suggested for {request.imei}")
    
    return ConnectResponse(status="success", data=response_data)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bts_id": BTS_ID,
        "location": {"x": BTS_LOCATION_X, "y": BTS_LOCATION_Y},
        "redis": "connected" if redis_client.ping() else "disconnected"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": f"BTS Service - {BTS_ID}",
        "lac": BTS_LAC,
        "location": {"x": BTS_LOCATION_X, "y": BTS_LOCATION_Y}
    }
