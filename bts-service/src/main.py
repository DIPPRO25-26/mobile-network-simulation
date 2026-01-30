"""
BTS Service - Base Transceiver Station Simulation

MVP Implementation using FastAPI and Redis with HMAC authentication
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
import hmac
import hashlib
from .broadcaster import Broadcaster
from .bts_status_poller import BtsStatusPoller
from .bts_status_sender import BtsStatusSender
from .user_presence_checker import UserPresenceChecker
from .observers.redis_cache import UserRedisCache, BtsInformationRedisCache, BtsStatusRedisCache


# -----------------------------------------------------------------------------------------------------
# Configuration From Environment Variables
# -----------------------------------------------------------------------------------------------------


BTS_ID = os.getenv("BTS_ID", "bts-1")
BTS_LAC = os.getenv("BTS_LAC", "1001")
BTS_LOCATION_X = float(os.getenv("BTS_LOCATION_X", "100"))
BTS_LOCATION_Y = float(os.getenv("BTS_LOCATION_Y", "100"))
CENTRAL_API_URL = os.getenv("CENTRAL_API_URL", "http://localhost:8080")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
MCC = os.getenv("MCC", "219")  # Croatia
MNC = os.getenv("MNC", "01")
HMAC_SECRET = os.getenv("HMAC_SECRET_KEY", "your_shared_secret_key_here")
BTS_MAX_USER_CAPACITY = int(os.getenv("BTS_MAX_USER_CAPACITY", "100"))
POLL_FOR_NEIGHBOUR_BTS_INFO_INTERVAL = int(os.getenv("POLL_FOR_NEIGHBOUR_BTS_INFO_INTERVAL", "5"))
BTS_NEIGHBOR_RADIUS = int(os.getenv("BTS_NEIGHBOR_RADIUS", "500"))
BTS_OVERLOAD_THRESHOLD = float(os.getenv("BTS_OVERLOAD_THRESHOLD", "0.8"))
# BTS_HANGOVER_DISTANCE_THRESHOLD = int(os.getenv("HANGOVER_DISTANCE_THRESHOLD", "150"))

USER_KEEP_ALIVE_INTERVAL = int(os.getenv("USER_KEEP_ALIVE_INTERVAL", "3")) # seconds
STATUS_SENDER_INTERVAL = int(os.getenv("STATUS_SENDER_INTERVAL", "5")) # seconds
USER_PRESENCE_CHECKER_INTERVAL = int(os.getenv("USER_PRESENCE_CHECKER_INTERVAL", "4")) # seconds

USER_INFORMATION_TTL = USER_KEEP_ALIVE_INTERVAL * 3 # seconds
BTS_NEIGBOUR_INFORMATION_TTL = POLL_FOR_NEIGHBOUR_BTS_INFO_INTERVAL * 3 # seconds
BTS_STATUS_TTL = STATUS_SENDER_INTERVAL * 3 # seconds


# -----------------------------------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------------------------------


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title=f"BTS Service - {BTS_ID}")

# Initialize Broadcaster
broadcaster = Broadcaster()

# Initialize Neighbour BTS Status Poller
neighbour_bts_status_poller = BtsStatusPoller

# Initialize BTS Status Sender
bts_status_sender = BtsStatusSender

# Initialize User Presence Checker
user_presence_checker = UserPresenceChecker

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

observers = []
user_redis_cache = None
bts_information_redis_cache = None
bts_status_redis_cache = None

STATUS = ["active", "inactive", "overloaded", "unknown"]


# -----------------------------------------------------------------------------------------------------
# Application Events
# -----------------------------------------------------------------------------------------------------


@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup"""
    logger.info(f"Starting BTS Service {BTS_ID}")

    # Initialize Redis observers
    global user_redis_cache
    user_redis_cache = UserRedisCache(redis_client=redis_client, ttl=USER_INFORMATION_TTL, owner_bts_id=BTS_ID)
    observers.append(user_redis_cache)

    global bts_information_redis_cache
    bts_information_redis_cache = BtsInformationRedisCache(redis_client=redis_client, ttl=BTS_NEIGBOUR_INFORMATION_TTL, owner_bts_id=BTS_ID)

    global bts_status_redis_cache
    bts_status_redis_cache = BtsStatusRedisCache(redis_client=redis_client, ttl=BTS_STATUS_TTL, owner_bts_id=BTS_ID)

    global bts_status_sender
    bts_status_sender = BtsStatusSender(
        send_bts_status_to_central_backend_async=send_bts_status_to_central_backend,
        cache=bts_status_redis_cache,
        owner_bts_id=BTS_ID,
        send_interval=STATUS_SENDER_INTERVAL
    )

    global neighbour_bts_status_poller
    neighbour_bts_status_poller = BtsStatusPoller(
        fetch_all_bts_info_async=get_all_bts_information_from_central_backend,
        observer=bts_information_redis_cache,
        owner_bts_id=BTS_ID,
        poll_interval=POLL_FOR_NEIGHBOUR_BTS_INFO_INTERVAL
    )

    global user_presence_checker
    user_presence_checker = UserPresenceChecker(
        user_cache=user_redis_cache,
        bts_status_cache=bts_status_redis_cache,
        owner_bts_id=BTS_ID,
        capacity=BTS_MAX_USER_CAPACITY,
        overload_threshold=BTS_OVERLOAD_THRESHOLD,
        check_interval=USER_PRESENCE_CHECKER_INTERVAL
    )

    # Prepare initial BTS information
    initial_bts_information = {
        "btsId": BTS_ID,
        "mcc": MCC,
        "mnc": MNC,
        "lac": BTS_LAC,
        "locationX": BTS_LOCATION_X,
        "locationY": BTS_LOCATION_Y,
        "status": "active",
        "maxCapacity": BTS_MAX_USER_CAPACITY,
        "currentLoad": 0
    }

    # Send initial BTS information to Central Backend
    await send_bts_information_to_central_backend(initial_bts_information)
    logger.info("Initial BTS information sent to Central Backend")

    # Cache initial BTS status
    bts_status_redis_cache.set_status(BTS_ID, "active", BTS_MAX_USER_CAPACITY, 0)

    # Start broadcaster thread
    broadcaster.start()
    logger.info("Broadcaster started")

    # Start bts status sender thread
    bts_status_sender.start()
    logger.info("BTS Status Sender started")

    # Start neighbour BTS status poller thread
    neighbour_bts_status_poller.start()
    logger.info("Neighbour BTS Status Poller started")

    # Start user presence checker thread
    user_presence_checker.start_checking()
    logger.info("User Presence Checker started")

@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on shutdown"""
    logger.info(f"Shutting down BTS Service {BTS_ID}")
    broadcaster.stop()


# -----------------------------------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------------------------------


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


class KeepAliveRequest(BaseModel):
    imei: str = Field(..., min_length=15, max_length=15, description="IMEI number")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    user_location: UserLocation


class KeepAliveResponse(BaseModel):
    status: str
    data: dict


class BtsInfo(BaseModel):
    bts_id: str
    lac: str
    location_x: float
    location_y: float


class StatusBtsInfo(BaseModel):
    bts_id: str
    capacity: int
    current_load: int


# -----------------------------------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------------------------------


def generate_hmac_signature(secret: str, body: str, timestamp: str) -> str:
    """Generate HMAC-SHA256 signature for request"""
    message = body + timestamp  # Match Java backend
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return signature.hex()


def notify_observers(event: str, data: dict):
    """Notify all observers of an event"""
    for observer in observers:
        observer.update(event=event, data=data)


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance between two points"""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

def calculate_signal_strength(distance: float, bts_range: float) -> float:
    """Calculate signal strength based on distance and BTS range"""
    if distance >= bts_range:
        return 0.0
    return (1 - (distance / bts_range) ** 2)


def should_handover(user_location: UserLocation) -> tuple[bool, Optional[str]]:
    distance_from_bts_to_user = calculate_distance(
        BTS_LOCATION_X, BTS_LOCATION_Y,
        user_location.x, user_location.y
    )

    # range of [0.0, 1.0], higher is better
    # 1.0 = at BTS, 0.0 = at edge of BTS range
    signal_strength_for_user = calculate_signal_strength(
        distance_from_bts_to_user,
        BTS_RANGE
    )

    known_bts = bts_information_redis_cache.get_all()
    if not known_bts:
        # TODO No valid BTS found for handover --> should we disconnect user?
        return True, None
    
    # Find the valid BTS with the best signal strength for the user
    # Valid means within neighbor radius and not overloaded
    strongest_valid_bts_id = None
    strongest_signal_strength = signal_strength_for_user

    for bts in known_bts:
        bts_id = bts.get("btsId")
        if not bts_id or bts_id == BTS_ID:
            continue

        try:
            bts_x = float(bts.get("locationX") or 0.0)
            bts_y = float(bts.get("locationY") or 0.0)
        except ValueError:
            continue

        # TODO --> filter out non-neighbor BTS already when polling, not here
        # In real life, BTS far away should not be considered for handover
        # BTS should have a list of neighbor BTS, we are simulating that with distance here
        if calculate_distance(BTS_LOCATION_X, BTS_LOCATION_Y, bts_x, bts_y) > BTS_NEIGHBOR_RADIUS:
            continue

        try:
            capacity = float(bts.get("maxCapacity") or 0.0)
            current_load = float(bts.get("currentLoad") or 0.0)
        except ValueError:
            capacity, current_load = 0.0, 0.0

        if capacity > 0 and (current_load / capacity) >= BTS_OVERLOAD_THRESHOLD:
            continue
        
        # In real life, user would report its signal strength for neighbor BTS
        # Here we are simulating that by calculating distance from neighbor BTS to user
        # and deriving signal strength from that
        distance_from_neighbour_to_user = calculate_distance(bts_x, bts_y, user_location.x, user_location.y)
        signal_strength_for_user_at_neighbor = calculate_signal_strength(
            distance_from_neighbour_to_user,
            BTS_RANGE
        )
        if signal_strength_for_user_at_neighbor > strongest_signal_strength:
            strongest_signal_strength = signal_strength_for_user_at_neighbor
            strongest_valid_bts_id = bts_id

    return (True, strongest_valid_bts_id) if strongest_valid_bts_id else (False, None)


# -----------------------------------------------------------------------------------------------------
# Neighbour BTS Requests
# -----------------------------------------------------------------------------------------------------


async def notify_previous_bts_to_remove_user(previous_bts_id: str, imei: str) -> None:
    """Notify previous BTS to remove user from its cache"""
    try:
        previous_bts_url = f"http://{previous_bts_id}:8080/api/v1/user/remove"
        async with httpx.AsyncClient() as client:
            await client.post(
                previous_bts_url,
                json={"imei": imei},
                timeout=2.0
            )
            logger.info(f"Notified {previous_bts_id} to remove user {imei}")
    except Exception as e:
        logger.warning(f"Failed to notify {previous_bts_id} to remove user {imei}: {e}") 


# -----------------------------------------------------------------------------------------------------
# Central Backend Requests
# -----------------------------------------------------------------------------------------------------


async def send_user_information_to_central_backend(data: dict) -> dict:
    """
    Send user event to Central Backend with HMAC signature

    X-Timestamp sprječava replay attacks - stare zahtjeve ne mogu biti ponovno poslani
    """
    url = f"{CENTRAL_API_URL}/api/v1/user"

    # Generate timestamp (ISO 8601 format)
    timestamp = datetime.now().isoformat()

    # Serialize body to JSON string (consistent formatting)
    body_str = json.dumps(data, separators=(',', ':'), sort_keys=True)

    # Generate HMAC signature
    signature = generate_hmac_signature(HMAC_SECRET, body_str, timestamp)

    # Prepare headers
    headers = {
        "X-HMAC-Signature": signature,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                content=body_str.encode('utf-8'),  # Send as bytes
                headers=headers,
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to send data to Central: {e}")
            raise HTTPException(status_code=502, detail="Central Backend unreachable")
        
        
async def send_bts_information_to_central_backend(data: dict) -> dict:
    """
    Send BTS information to Central Backend with HMAC signature

    X-Timestamp sprječava replay attacks - stare zahtjeve ne mogu biti ponovno poslani
    """
    url = f"{CENTRAL_API_URL}/api/v1/bts"

    # Generate timestamp (ISO 8601 format)
    timestamp = datetime.now().isoformat()

    # Serialize body to JSON string (consistent formatting)
    body_str = json.dumps(data, separators=(',', ':'), sort_keys=True)

    # Generate HMAC signature
    signature = generate_hmac_signature(HMAC_SECRET, body_str, timestamp)

    # Prepare headers
    headers = {
        "X-HMAC-Signature": signature,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, content=body_str.encode("utf-8"), headers=headers, timeout=5.0)

        if response.status_code == 409:
            logger.info(f"BTS {data.get('btsId')} already registered (409). Continuing.")
            return response.json() if response.content else {"status": "conflict"}

        response.raise_for_status()
        return response.json()
    
    
async def send_bts_status_to_central_backend(bts_id: str, data: dict) -> dict:
    """
    Send BTS status to Central Backend with HMAC signature

    X-Timestamp sprječava replay attacks - stare zahtjeve ne mogu biti ponovno poslani
    """
    url = f"{CENTRAL_API_URL}/api/v1/bts/{bts_id}/status"

    # Generate timestamp (ISO 8601 format)
    timestamp = datetime.now().isoformat()

    # Serialize body to JSON string (consistent formatting)
    body_str = json.dumps(data, separators=(',', ':'), sort_keys=True)

    # Generate HMAC signature
    signature = generate_hmac_signature(HMAC_SECRET, body_str, timestamp)

    # Prepare headers
    headers = {
        "X-HMAC-Signature": signature,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.patch(url, content=body_str.encode("utf-8"), headers=headers, timeout=5.0)
        response.raise_for_status()
        return response.json()
        

async def get_all_bts_information_from_central_backend() -> dict:
    url = f"{CENTRAL_API_URL}/api/v1/bts"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get data from Central: {e}")
            raise HTTPException(status_code=502, detail="Central Backend unreachable")


# -----------------------------------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------------------------------


@app.post("/api/v1/connect", response_model=ConnectResponse)
async def connect_user(request: ConnectRequest):
    logger.info(f"User {request.imei} connecting to {BTS_ID}")

    # Check for handover need
    # needs_handover, target_bts = should_handover(request.user_location)

    if (calculate_distance(
        BTS_LOCATION_X, BTS_LOCATION_Y,
        request.user_location.x, request.user_location.y
    ) > BTS_RANGE):
        logger.warning(f"User {request.imei} is out of range for BTS {BTS_ID}")
        
        response_data = {
            "bts_id": BTS_ID,
            "action": "disconnect",
            "target_bts_id": None,
            "message": "User out of range"
        }
        return ConnectResponse(status="error", data=response_data)

    # Prepare data for Central Backend
    user_information = {
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

    # Send to Central Backend with HMAC signature
    central_response = await send_user_information_to_central_backend(user_information)
    previous_bts_id = central_response["data"]["previousLocation"]["btsId"]

    if previous_bts_id and previous_bts_id != BTS_ID:
        await notify_previous_bts_to_remove_user(previous_bts_id, request.imei)

    notify_observers(event="user_connected", data={
        "imei": request.imei,
        "location": {
            "x": request.user_location.x,
            "y": request.user_location.y
        },
        "bts_id": BTS_ID,
        "timestamp": request.timestamp
    })

    # Build response
    response_data = {
        "bts_id": BTS_ID,
        # "action": "handover" if needs_handover else None,
        "action": None,
        # "target_bts_id": target_bts if needs_handover else None,
        "target_bts_id": None,
        "message": "Connected successfully"
    }

    # if needs_handover:
    #     logger.warning(f"Handover suggested for {request.imei} to BTS {target_bts}")

    return ConnectResponse(status="success", data=response_data)

@app.post("/api/v1/keepalive", response_model=KeepAliveResponse)
async def keepalive_user(request: KeepAliveRequest):
    logger.info(f"User {request.imei} sending keep-alive to {BTS_ID}")

    distance_from_bts_to_user = calculate_distance(
        BTS_LOCATION_X, BTS_LOCATION_Y,
        request.user_location.x, request.user_location.y
    )
    if distance_from_bts_to_user > BTS_RANGE: 
        logger.warning(f"User {request.imei} is out of range for BTS {BTS_ID}")
        response_data = {
            "bts_id": BTS_ID,
            "action": "disconnect",
            "target_bts_id": None,
            "message": "User out of range"
        }
        return ConnectResponse(status="failure", data=response_data)
    
    # Check for handover need
    needs_handover, target_bts = should_handover(request.user_location)
    
    # Prepare data for Central Backend
    user_information = {
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
    central_response = await send_user_information_to_central_backend(user_information)
    
    notify_observers(event="user_keepalive", data={
        "imei": request.imei,
        "location": {
            "x": request.user_location.x,
            "y": request.user_location.y
        },
        "bts_id": BTS_ID,
        "timestamp": request.timestamp
    })
    
    # Build response
    response_data = {
        "bts_id": BTS_ID,
        "action": "handover" if needs_handover else None,
        "target_bts_id": target_bts if needs_handover else None,
        "message": "Keep-alive successful"
    }
    
    if needs_handover:
        logger.warning(f"Handover suggested for {request.imei}")
    
    return KeepAliveResponse(status="success", data=response_data)


@app.post("/api/v1/user/remove")
async def remove_user(payload: dict):
    imei = payload.get("imei")
    if not imei:
        logger.error("IMEI not provided for user removal")
        return {"status": "error", "message": "IMEI not provided"}

    logger.info(f"Removing user {imei} from BTS {BTS_ID}")
    
    if user_redis_cache:
        if (user_redis_cache.is_imei_connected(imei)):
            user_redis_cache.remove_connected_imei(imei)
            logger.info(f"User {imei} removed from the list of connected users in {BTS_ID}")
        else:
            logger.info(f"User {imei} not found in the list of connected users in {BTS_ID}")
            return {"status": "success", "message": f"User {imei} not found in {BTS_ID}"}
    
    return {"status": "success", "message": f"User {imei} removed from {BTS_ID}"}


@app.post("/api/v1/shutdown")
async def shutdown_bts(payload: dict):
    reason = payload.get("reason", "requested")
    requested_by = payload.get("requestedBy", "central-backend")
    logger.warning(f"Shutdown requested for {BTS_ID} by {requested_by}. Reason: {reason}")

    try:
        broadcaster.stop()
    except Exception:
        pass

    try:
        neighbour_bts_status_poller.stop()
    except Exception:
        pass

    try:
        bts_status_sender.stop()
    except Exception:
        pass

    try:
        user_presence_checker.stop_checking()
    except Exception:
        pass

    try:
        redis_client.close()
    except Exception:
        pass

    os._exit(0)

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
