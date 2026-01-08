# API Specifikacija

## Central Backend API

Base URL: `http://localhost:8080/api/v1`

### 1. POST /user - Prijem korisničkih podataka

BTS šalje informaciju o novom korisniku ili promjeni lokacije.

**Request:**
```json
{
  "imei": "123456789012345",
  "mcc": "219",
  "mnc": "01",
  "lac": "1001",
  "bts_id": "BTS001",
  "timestamp": "2025-01-08T10:30:00Z",
  "user_location": {
    "x": 100.5,
    "y": 200.3
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "previous_location": {
      "bts_id": "BTS002",
      "lac": "1001",
      "last_seen": "2025-01-08T10:25:00Z"
    },
    "cdr_id": 12345
  }
}
```

**Headers:**
- `X-HMAC-Signature` - HMAC potpis tijela zahtjeva
- `X-Timestamp` - Unix timestamp zahtjeva
- `Content-Type: application/json`

---

### 2. GET /cdr - Dohvat CDR zapisa

Dohvat CDR zapisa s filterima za analitiku i vizualizaciju.

**Query Parameters:**
- `imei` (optional) - Filtriraj po IMEI broju
- `bts_id` (optional) - Filtriraj po BTS ID
- `lac` (optional) - Filtriraj po LAC zoni
- `from` (optional) - Od datuma (ISO 8601)
- `to` (optional) - Do datuma (ISO 8601)
- `limit` (optional) - Broj zapisa (default: 100, max: 1000)
- `offset` (optional) - Offset za paginaciju

**Example:**
```
GET /cdr?bts_id=BTS001&from=2025-01-08T00:00:00Z&limit=50
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "records": [
      {
        "id": 12345,
        "imei": "123456789012345",
        "mcc": "219",
        "mnc": "01",
        "lac": "1001",
        "bts_id": "BTS001",
        "previous_bts_id": "BTS002",
        "timestamp_arrival": "2025-01-08T10:30:00Z",
        "timestamp_departure": "2025-01-08T10:35:00Z",
        "distance": 150.5,
        "speed": 30.1,
        "duration": 300
      }
    ],
    "total": 1,
    "limit": 50,
    "offset": 0
  }
}
```

---

### 3. GET /alerts - Dohvat anomalija

Dohvat detektiranih anomalija.

**Query Parameters:**
- `alert_type` (optional) - Tip anomalije (flapping, overload, abnormal_speed)
- `severity` (optional) - Razina ozbiljnosti (low, medium, high, critical)
- `from` (optional) - Od datuma
- `to` (optional) - Do datuma
- `resolved` (optional) - true/false - samo riješene/neriješene

**Response:**
```json
{
  "status": "success",
  "data": {
    "alerts": [
      {
        "id": 456,
        "alert_type": "abnormal_speed",
        "severity": "high",
        "imei": "123456789012345",
        "bts_id": "BTS001",
        "description": "User traveling at 200 km/h",
        "detected_at": "2025-01-08T10:35:00Z",
        "resolved_at": null,
        "metadata": {
          "speed": 200.5,
          "threshold": 120.0
        }
      }
    ],
    "total": 1
  }
}
```

---

### 4. GET /health - Health check

Provjera statusa servisa.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T10:30:00Z",
  "services": {
    "database": "up",
    "redis": "up"
  }
}
```

---

## BTS Service API

Base URL: `http://localhost:808X/api/v1` (8081, 8082, 8083)

### POST /connect - Korisnik se spaja na BTS

Simulator šalje podatke o korisniku koji se spaja na BTS.

**Request:**
```json
{
  "imei": "123456789012345",
  "timestamp": "2025-01-08T10:30:00Z",
  "user_location": {
    "x": 100.5,
    "y": 200.3
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "bts_id": "BTS001",
    "action": null,
    "message": "Connected successfully"
  }
}
```

Ako korisnik treba promijeniti BTS:
```json
{
  "status": "success",
  "data": {
    "bts_id": "BTS001",
    "action": "handover",
    "target_bts_id": "BTS002",
    "reason": "Better signal strength"
  }
}
```

---

## Error Responses

Svi API-ji koriste standardne error response:

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_HMAC",
    "message": "HMAC signature validation failed",
    "details": {}
  }
}
```

**Error Codes:**
- `INVALID_HMAC` - HMAC validacija neuspješna
- `TIMESTAMP_EXPIRED` - Zahtjev je istekao
- `INVALID_REQUEST` - Neispravni podaci
- `NOT_FOUND` - Resurs nije pronađen
- `INTERNAL_ERROR` - Greška na serveru

---

## Security

Svi zahtjevi prema Central Backend i BTS servisima moraju sadržavati HMAC potpis.

### HMAC Generiranje

```python
import hmac
import hashlib
import time
import json

secret_key = "your-secret-key"
timestamp = int(time.time())
body = json.dumps(payload)

message = f"{timestamp}.{body}"
signature = hmac.new(
    secret_key.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    "X-HMAC-Signature": signature,
    "X-Timestamp": str(timestamp),
    "Content-Type": "application/json"
}
```

### Validacija (server side)

1. Provjeri da je `X-Timestamp` unutar 5 minuta
2. Rekonstruiraj poruku: `{timestamp}.{body}`
3. Izračunaj HMAC potpis s tajnim ključem
4. Usporedi s `X-HMAC-Signature`
