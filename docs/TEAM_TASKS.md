# Team Tasks - Phase 2 (MVP Extension)

## ✅ Što je već napravljeno (MVP)

### Central Backend
- ✅ Maven projekt setup
- ✅ Spring Boot aplikacija
- ✅ CDRRecord JPA entity
- ✅ CDRRepository s osnovnim queryjima
- ✅ UserService - business logika
- ✅ UserController - POST /api/v1/user endpoint
- ✅ Dockerfile
- ✅ application.properties

**Radi:** Prim podatke od BTS-a, sprema CDR zapise, vraća prethodnu lokaciju

### BTS Service
- ✅ FastAPI Python aplikacija
- ✅ POST /api/v1/connect endpoint
- ✅ Redis caching aktivnih korisnika
- ✅ Komunikacija s Central Backendom
- ✅ Osnovna handover logika (distance-based)
- ✅ Dockerfile
- ✅ Health check endpoints

**Radi:** Prima događaje od simulatora, šalje Central-u, cachira u Redis

---

## 🎯 Što treba dodati - Po timovima

### 1. Central Backend Tim (Ante, Nikola V., Leon)

#### Priority 1 - Do 15.11.
- [ ] **Izračunavanje distance, speed, duration**
  - Implementirati metode u `UserService.java`:
    - `calculateDistance()` - Euclidean ili haversine formula
    - `calculateSpeed()` - brzina = distance / time
    - `calculateDuration()` - trajanje između timestampova
  
- [ ] **GET /api/v1/cdr endpoint**
  - Dohvat CDR zapisa s filterima
  - Parametri: `imei`, `btsId`, `lac`, `from`, `to`, `limit`, `offset`
  - Pagination support

#### Priority 2 - Do 20.11.
- [ ] **GET /api/v1/alerts endpoint**
  - Kreirati `Alert` entity i repository
  - Endpoint za dohvat anomalija
  
- [ ] **HMAC validacija middleware**
  - Kreirati `HmacValidator` klasu
  - Filter koji provjerava `X-HMAC-Signature` header
  - Timestamp validacija (max 5 min stara)
  
- [ ] **Error handling**
  - `@ControllerAdvice` za globalno error handling
  - Custom exception klase
  - Proper HTTP status kodovi

- [ ] **Unit testovi**
  - UserService testovi
  - Repository testovi s H2 in-memory DB

**Datoteke za dodati:**
- `src/main/java/fer/project/central/model/Alert.java`
- `src/main/java/fer/project/central/repository/AlertRepository.java`
- `src/main/java/fer/project/central/controller/CDRController.java`
- `src/main/java/fer/project/central/security/HmacValidator.java`
- `src/main/java/fer/project/central/exception/GlobalExceptionHandler.java`
- `src/test/java/...`

---

### 2. BTS Service Tim (Matija, Nikola V.)

#### Priority 1 - Do 15.11.
- [ ] **HMAC signing za zahtjeve prema Centralu**
  - Implementirati `sign_request()` funkciju
  - Dodati X-HMAC-Signature i X-Timestamp headere
  
- [ ] **Lokalna analitika**
  - Računanje brzine kretanja korisnika
  - Brojanje prijelaza između BTS-ova
  - Cache historical data za kalkulacije

#### Priority 2 - Do 20.11.
- [ ] **Napredna handover logika**
  - Query BTS registry iz baze za susjedne BTS-ove
  - Pronalaženje najbližeg BTS-a
  - Simulacija jačine signala
  - Provjera kapaciteta BTS-a

- [ ] **Retry logika s exponential backoff**
  - Retry za neuspjele zahtjeve prema Centralu
  - Circuit breaker pattern

- [ ] **Redis optimizacije**
  - Bulk operations
  - TTL strategija
  - Cache invalidation

- [ ] **Unit testovi**
  - pytest za endpoint-e
  - Mock Redis i Central API

**Datoteke za dodati:**
- `src/security.py` - HMAC funkcije
- `src/analytics.py` - Lokalna analitika
- `src/handover.py` - Handover logika
- `src/config.py` - Configuration management
- `tests/` directory

---

### 3. Security Tim (Jana, Ivan)

#### Priority 1 - Do 10.11.
- [ ] **HMAC implementation - Python verzija**
  - Kreirati `security/hmac_utils.py`
  - `generate_hmac()` funkcija
  - `validate_hmac()` funkcija
  - Timestamp provjera

- [ ] **HMAC implementation - Java verzija**
  - `HmacValidator.java` klasa
  - Integration s Spring Security

#### Priority 2 - Do 20.11.
- [ ] **mTLS certifikati**
  - Test certifikati za development
  - Integration s BTS i Central services
  
- [ ] **Audit log**
  - Logger middleware za sve API pozive
  - Spremanje u `audit_log` tablicu
  - Query interface za pregled logova

**Datoteke za dodati:**
- `security/hmac_utils.py`
- `central-backend/src/main/java/fer/project/central/security/HmacValidator.java`
- `central-backend/src/main/java/fer/project/central/security/AuditLogger.java`
- `security/README.md` - Usage instructions

---

### 4. Analytics Tim (Nikola P., Jurica)

#### Priority 1 - Do 15.11.
- [ ] **Python analytics module setup**
  - `analytics/src/db_connector.py` - PostgreSQL connection
  - `analytics/src/data_loader.py` - Load CDR data
  - `analytics/requirements.txt`

- [ ] **Feature engineering**
  - Definirati značajke za anomaly detection:
    - Brzina kretanja
    - Broj prijelaza u vremenu
    - Vrijeme provedeno na BTS-u
    - Flapping detection (česti prijelazi)

#### Priority 2 - Do 20.12.
- [ ] **Anomaly detection algorithms**
  - Rule-based: brzina > threshold, flapping
  - Statistical: z-score za outliers
  - Spremanje alertova u `alerts` tablicu

- [ ] **Jupyter notebooks**
  - Analiza CDR podataka
  - Vizualizacija anomalija
  - Performance evaluacija

**Datoteke za dodati:**
- `analytics/src/__init__.py`
- `analytics/src/db_connector.py`
- `analytics/src/data_loader.py`
- `analytics/src/anomaly_detection/rules.py`
- `analytics/src/anomaly_detection/statistical.py`
- `analytics/notebooks/cdr_analysis.ipynb`
- `analytics/requirements.txt`

---

### 5. Visualization Tim (Jurica, Nikola P.)

#### Priority 1 - Do 15.11.
- [ ] **Grafana datasource configuration**
  - `visualization/datasources/postgres.yml`
  - Connection na PostgreSQL

- [ ] **Basic dashboards**
  - Broj korisnika po BTS-u (timeline)
  - Broj prijelaza između BTS-ova
  - Top active users (by IMEI)

#### Priority 2 - Do 20.12.
- [ ] **Advanced dashboards**
  - Heatmap BTS opterećenja
  - Anomaly alerts panel
  - User trajectory visualization
  - LAC area map

**Datoteke za dodati:**
- `visualization/datasources/postgres.yml`
- `visualization/dashboards/network-overview.json`
- `visualization/dashboards/anomalies.json`
- `visualization/dashboards/user-activity.json`

---

### 6. Simulator Tim (Preddiplomski)

**Nota:** Simulator već ima specifikaciju. Koordinirajte s diplomskim timom za integraciju.

#### Potrebno:
- [ ] POST requests prema BTS `/api/v1/connect`
- [ ] Generate proper IMEI brojeve
- [ ] Simulate user movement (random walk)
- [ ] Frontend za pokretanje simulacije

---

## 📋 Testiranje integracije

Nakon što svaki tim dovrši Priority 1 zadatke, testirajte end-to-end:

```bash
# 1. Pokreni sve servise
docker-compose up -d

# 2. Provjeri health
curl http://localhost:8080/api/v1/user/health
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8083/health

# 3. Test simulator -> BTS -> Central flow
# (Simulirajte zahtjev ručno ili preko simulatora)

# 4. Provjeri CDR zapise u bazi
docker exec -it mobile-network-db psql -U admin -d mobile_network -c "SELECT * FROM cdr_records LIMIT 10;"
```

---

## 🚀 Workflow

1. **Kloniraj repo** i kreiraj branch
   ```bash
   git checkout -b feature/central-backend-distance-calculation
   ```

2. **Implementiraj feature** (vidi TODO komentare u kodu!)

3. **Testiraj lokalno**

4. **Commit i push**
   ```bash
   git commit -m "feat: implement distance calculation in UserService"
   git push origin feature/central-backend-distance-calculation
   ```

5. **Otvori Pull Request** na GitHubu

6. **Code review** od drugog člana tima

7. **Merge** u main

---

## ❓ Pitanja ili problemi?

- Discord kanal
- GitHub Issues
- Voditelj tima ili Roko (projekt leader)

**Sretno! 🎉**
