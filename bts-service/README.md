# BTS Service

Servis koji simulira bazne stanice (Base Transceiver Station). Svaka BTS instanca ima jedinstveni ID, fiksnu lokaciju i pokriva određeno LAC područje.

## Odgovornosti

- Prijem događaja od simulatora (korisnik se spaja)
- Lokalni Redis cache aktivnih korisnika
- Slanje podataka centralnom servisu
- Odlučivanje o handover-u (prebacivanje na drugu stanicu)
- Lokalna analitika (brzina kretanja, broj prijelaza)

## Tim

- **Matija Alojz Stuhne** - Voditelj, implementacija core logike
- **Nikola Vlahović** - Cache mehanizam i integracija

## Tehnologije

**Opcija 1: Java/Spring Boot**
- Spring Boot
- Redis client
- RestTemplate za komunikaciju

**Opcija 2: Python/FastAPI**
- FastAPI
- Redis-py
- httpx/requests za komunikaciju

**Opcija 3: Go**
- Go standard library
- go-redis
- net/http

**Odluka:** TBD na prvom timskom sastanku

## Arhitektura

```
Simulator → BTS Service → Central Backend
              ↓
           Redis Cache
```

### BTS Instance Configuration

Svaka BTS instanca konfigurira se environment varijablama:

```bash
BTS_ID=BTS001           # Jedinstveni ID
BTS_LAC=1001            # Location Area Code
BTS_LOCATION_X=100      # X koordinata
BTS_LOCATION_Y=100      # Y koordinata
CENTRAL_API_URL=http://central-backend:8080
REDIS_HOST=redis
```

## API Endpoints

### POST /api/v1/connect

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

**Response (normalno):**
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

**Response (handover potreban):**
```json
{
  "status": "success",
  "data": {
    "bts_id": "BTS001",
    "action": "handover",
    "target_bts_id": "BTS002",
    "reason": "Better signal / User too far"
  }
}
```

## Redis Cache

BTS koristi Redis za lokalni cache aktivnih korisnika:

```
Key: bts:{BTS_ID}:active_users
Type: Hash
Fields:
  {IMEI} → JSON {last_seen, location, connection_count}

Expiration: 5 minuta
```

## Lokalna Analitika

BTS može lokalno računati:
- Brzinu kretanja korisnika
- Broj prijelaza između stanica
- Vrijeme provedeno u LAC zoni

## Docker Deployment

3-5 instanci se pokreću putem docker-compose:

```yaml
bts-1:
  environment:
    BTS_ID: BTS001
    BTS_LAC: "1001"
    BTS_LOCATION_X: 100
    BTS_LOCATION_Y: 100
  ports:
    - "8081:8080"
```

## Razvoj

### Lokalno (bez Dockera)

```bash
# Pokreni Redis
docker-compose up -d redis

# Postavi env varijable
export BTS_ID=BTS001
export BTS_LAC=1001
export BTS_LOCATION_X=100
export BTS_LOCATION_Y=100
export CENTRAL_API_URL=http://localhost:8080
export REDIS_HOST=localhost
export HMAC_SECRET_KEY=your-secret-key

# Pokreni servis (ovisno o tehnologiji)
# Java: ./mvnw spring-boot:run
# Python: uvicorn main:app --reload
# Go: go run main.go
```

## Handover Logika

BTS odlučuje o handoveru temeljem:

1. **Udaljenost** - ako je korisnik daleko od BTS lokacije
2. **Jačina signala** (simulirana) - može se dodati kao feature
3. **Opterećenje BTS-a** - prebaci na manje opterećenu stanicu

```python
def should_handover(user_location, bts_location):
    distance = calculate_distance(user_location, bts_location)
    if distance > MAX_DISTANCE_THRESHOLD:
        # Find nearest BTS
        return True, nearest_bts_id
    return False, None
```

## Faza 2 - Trenutni zadaci

- [ ] Odluka o tehnologiji (Java/Python/Go)
- [ ] Implementacija POST /connect endpointa
- [ ] Redis cache integracija za aktivne korisnike
- [ ] Komunikacija s Central Backend-om (POST /user)
- [ ] HMAC potpis zahtjeva
- [ ] Testiranje 3 instance paralelno u Docker Compose

**Deadline:** 20.11.2025

## Faza 3 - Sljedeći zadaci

- Lokalna analitika (brzina, prijelazi)
- Handover logika
- Redis cache optimizacije
- 5 instanci u Docker Compose
