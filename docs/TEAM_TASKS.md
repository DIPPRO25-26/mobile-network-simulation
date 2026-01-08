# Team Tasks - Phase 2 (MVP Extension)

> **Cilj:** Implementirati MINIMALNO POTREBNO da ispunimo zahtjeve projekta
> **Princip:** KISS - Keep It Simple, Stupid!

## ✅ Što je već napravljeno (MVP - ~40% projekta)

### Central Backend
- ✅ Maven projekt setup
- ✅ Spring Boot aplikacija
- ✅ CDRRecord JPA entity s @Column annotations
- ✅ CDRRepository s osnovnim queryjima
- ✅ UserService - business logika za prijem događaja
- ✅ UserController - POST /api/v1/user endpoint
- ✅ Dockerfile (eclipse-temurin:17-jre)
- ✅ PostgreSQL integracija
- ✅ Docker network komunikacija

**Radi:** Prima podatke od BTS-a, sprema CDR zapise, vraća prethodnu lokaciju

### BTS Service
- ✅ FastAPI Python aplikacija
- ✅ POST /api/v1/connect endpoint
- ✅ Redis caching aktivnih korisnika
- ✅ Komunikacija s Central Backendom (Docker network)
- ✅ Osnovna handover logika (distance-based)
- ✅ Dockerfile
- ✅ Health check endpoints
- ✅ 3 BTS instance (BTS001, BTS002, BTS003)

**Radi:** Prima događaje od simulatora, šalje Central-u, cachira u Redis, detektira handover

### Infrastruktura
- ✅ PostgreSQL database (5 tablica: cdr_records, alerts, user_activity, bts_registry, audit_log)
- ✅ Redis cache
- ✅ Docker Compose partial setup
- ✅ GitHub repository s dokumentacijom

---

## 🎯 Što treba dodati - MINIMALNI zahtjevi

### 1️⃣ Central Backend Tim (Ante Prkačin, Nikola Vlahović, Leon Lakić)

**Ante Prkačin:**
- [ ] **Dodati polja u CDR model:**
  - `duration` (BIGINT) - trajanje u sekundama
  - `distance` (DECIMAL) - udaljenost u metrima
  - `speed` (DECIMAL) - brzina u m/s
  - Implementirati kalkulacije u `UserService.java`
  
- [ ] **GET /api/v1/cdr endpoint:**
  - Parametri: `imei`, `btsId`, `from` (datum), `to` (datum), `limit`
  - Pagination (jednostavna - offset/limit)
  - Vraća JSON array CDR zapisa
  
- [ ] **Unit testovi:**
  - `UserServiceTest.java` - testovi za kalkulacije
  - `CDRControllerTest.java` - testovi za endpoint
  
- [ ] **API dokumentacija** (u `docs/API.md`)

**Nikola Vlahović:**
- [ ] **Dodati polja u bazu:**
  - `lac` (VARCHAR) - Location Area Code
  - `mcc` (VARCHAR) - Mobile Country Code
  - `mnc` (VARCHAR) - Mobile Network Code
  - Ažurirati `schema.sql`
  
- [ ] **Schema migration:**
  - ALTER TABLE statements
  - Update CDRRecord entity s novim poljima
  
- [ ] **Integracija s BTS timom:**
  - Koordinacija API formata
  - Testiranje izmjena
  
- [ ] **Integration testovi** (end-to-end flow)

**Leon Lakić:**
- [ ] **Input validacija:**
  - IMEI format check (15 znamenki, Luhn checksum)
  - Timestamp validacija (ne starije od 1h, ne u budućnosti)
  - Lokacija validacija (X, Y unutar grida)
  
- [ ] **Error handling:**
  - `@ControllerAdvice` za globalno exception handling
  - Custom exception klase (InvalidIMEIException, itd.)
  - Proper HTTP status codes (400, 404, 500)
  
- [ ] **Performance optimization:**
  - Database indices na `imei`, `bts_id`, `timestamp`
  - Query optimization
  
- [ ] **Deployment docs** (`docs/DEPLOYMENT.md`)

**Datoteke za dodati/modificirati:**
```
central-backend/
├── src/main/java/fer/project/central/
│   ├── controller/CDRController.java              (NOVO)
│   ├── service/UserService.java                   (UPDATE - kalkulacije)
│   ├── model/CDRRecord.java                       (UPDATE - nova polja)
│   ├── exception/GlobalExceptionHandler.java      (NOVO)
│   └── exception/InvalidIMEIException.java        (NOVO)
├── src/main/resources/
│   └── schema.sql                                 (UPDATE - nova polja)
└── src/test/java/                                 (NOVO - testovi)
```

---

### 2️⃣ BTS Service Tim (Matija Alojz Stuhne, Nikola Vlahović)

**Matija Alojz Stuhne:**
- [ ] **Dodati LAC environment variable:**
  - `LAC` env var u Docker Compose
  - Svaki BTS ima svoj LAC (BTS001=1001, BTS002=1001, BTS003=1002)
  - Slanje LAC-a u zahtjevu prema Centralu
  
- [ ] **Automatski handover:**
  - Kalkulacija udaljenosti do svih BTS-ova
  - Ako je korisnik bliži drugom BTS-u (>threshold), vrati `handover` akciju
  - Response: `{"action": "handover", "target_bts_id": "BTS002"}`
  
- [ ] **Testiranje handover scenarija:**
  - Simulirati korisnika koji prelazi između BTS-ova
  - Verificirati da handover radi ispravno
  - Load test s 10+ korisnika
  
- [ ] **BTS dokumentacija** (`bts-service/README.md`)

**Nikola Vlahović (dodatno uz Central Backend):**
- [ ] **Lokalna detekcija anomalija:**
  - **Prevelika brzina:** ako je brzina > 200 km/h (55.56 m/s), reject zahtjev
  - **Duplikat korisnika:** ako je isti IMEI aktivan na drugom BTS-u, alert
  - Kreirati `anomaly_detection.py` modul
  
- [ ] **Redis cache s TTL:**
  - Postaviti TTL od 1h za sve korisničke zapise
  - Dodati metadata: `last_seen_timestamp`, `location`, `speed`
  
- [ ] **Load testiranje:**
  - Testirati s 100+ simultanih korisnika
  - Mjeriti response time i throughput
  - Dokumentirati rezultate

**Datoteke za dodati/modificirati:**
```
bts-service/
├── src/
│   ├── main.py                    (UPDATE - LAC support)
│   ├── anomaly_detection.py       (NOVO)
│   ├── handover.py                (NOVO)
│   └── config.py                  (UPDATE - LAC config)
├── tests/                     (NOVO)
└── README.md                  (UPDATE)
```

---

### 3️⃣ Data Analysis & Anomaly Detection (Nikola Petrović, Jurica Galić)

**Nikola Petrović:**
- [ ] **Centralni anomaly detector** (Python script):
  - **Flapping detection:** korisnik se vraća između 2 BTS-a >5 puta/sat
  - **Abnormal speed:** brzina > 200 km/h (izračunato iz distance/time)
  - **BTS overload:** >50 korisnika na jednom BTS-u istovremeno
  - SQL upiti za dohvat podataka iz `cdr_records`
  
- [ ] **Spremanje u alerts tablicu:**
  - INSERT statements za detektirane anomalije
  - Struktura: `alert_type`, `imei`, `bts_id`, `severity`, `description`, `timestamp`
  
- [ ] **Testiranje:**
  - Simulirati anomalne scenarije
  - Verificirati da se alertovi spremaju
  - Dokumentirati false positive/negative rate

**Jurica Galić:**
- [ ] **SQL upiti za metrike:**
  - Broj korisnika po BTS-u (GROUP BY bts_id)
  - Prosečna brzina kretanja (AVG speed)
  - Broj handovera (COUNT WHERE previous_bts_id IS NOT NULL)
  - LAC coverage (COUNT DISTINCT korisnika po LAC-u)
  
- [ ] **Metrike za vizualizaciju:**
  - CSV export za Grafana
  - JSON format za REST API (opciono)
  
- [ ] **Dokumentacija algoritama** (`docs/ANOMALY_DETECTION.md`)

**Datoteke za dodati:**
```
analytics/
├── src/
│   ├── anomaly_detector.py        (NOVO - glavni script)
│   ├── db_connector.py            (NOVO - PostgreSQL connection)
│   ├── metrics_calculator.py      (NOVO - SQL upiti)
│   └── config.py                  (NOVO)
├── sql/
│   └── queries.sql                (NOVO - svi upiti)
├── requirements.txt           (NOVO - psycopg2, pandas)
└── README.md                  (NOVO)
```

---

### 4️⃣ Visualization & Metrics (Jurica Galić, Nikola Petrović)

**Jurica Galić:**
- [ ] **Grafana dashboardi** (4 panela):
  1. **Network Overview:** Broj korisnika po BTS-u (timeline chart)
  2. **Alerts:** Prikaz anomalija iz `alerts` tablice (table panel)
  3. **Handover Heatmap:** BTS→BTS matrica prijelaza
  4. **User Location Map:** Scatter plot X,Y koordinata korisnika
  
- [ ] **Datasource konfiguracija:**
  - PostgreSQL connection u Grafana
  - Test queries

**Nikola Petrović:**
- [ ] **Prometheus setup:**
  - `prometheus.yml` konfiguracija
  - Scraping BTS i Central metrics endpoints
  
- [ ] **Custom metrics exporter** (Python):
  - Export custom metrika (broj korisnika, handover rate)
  - `/metrics` endpoint za Prometheus

**Datoteke za dodati:**
```
visualization/
├── dashboards/
│   ├── network-overview.json      (NOVO)
│   └── anomalies.json             (NOVO)
├── datasources/
│   └── postgres.yml               (NOVO)
└── prometheus/
    └── prometheus.yml             (NOVO)
```

---

### 5️⃣ Security Layer (Jana Bulum, Ivan Đurić)

**Jana Bulum:**
- [ ] **HMAC potpis - Python implementacija** (za BTS servise):
  - Kreirati `security/hmac_utils.py`
  - `generate_hmac(message, secret)` funkcija (HMAC-SHA256)
  - Dodavanje `X-HMAC-Signature` i `X-Timestamp` headera u BTS zahtjeve
  
- [ ] **Timestamp validacija:**
  - Provjera da je timestamp svjež (<5 min)
  - Replay protection (ne prihvaća stare zahtjeve)
  
- [ ] **Shared secret management:**
  - Environment variable `HMAC_SECRET`
  - Dokumentacija kako postaviti secret
  
- [ ] **Security dokumentacija** (`security/README.md`)

**Ivan Đurić:**
- [ ] **HMAC validacija - Java implementacija** (za Central Backend):
  - `HmacValidator.java` klasa
  - Spring `@Component` koji provjerava potpis
  - Middleware za sve `/api/v1/user` zahtjeve
  
- [ ] **Audit log:**
  - Logger za sve BTS→Central zahtjeve
  - Spremanje u `audit_log` tablicu: `request_id`, `bts_id`, `endpoint`, `timestamp`, `status_code`
  - Query endpoint: GET /api/v1/audit
  
- [ ] **IMEI validacija:**
  - 15 znamenki check
  - Luhn checksum algoritam
  - Integration u UserController
  
- [ ] **Security testiranje:**
  - Pokus slanja zahtjeva bez HMAC-a (čekujemo 401)
  - Pokus slanja starog timestampa (čekujemo 403)
  - Pokus slanja nevaljanih IMEI brojeva (čekujemo 400)

**Datoteke za dodati:**
```
security/
├── hmac_utils.py              (NOVO - Python HMAC)
└── README.md                  (NOVO)

central-backend/src/main/java/fer/project/central/
├── security/
│   ├── HmacValidator.java     (NOVO)
│   └── AuditLogger.java       (NOVO)
└── validation/
    └── IMEIValidator.java     (NOVO)
```

---

### 6️⃣ Orkestracija & Dokumentacija (Roko Gligora)

- [ ] **Docker Compose dovršetak:**
  - Dodati Analytics service
  - Dodati Grafana i Prometheus
  - Environment variables za sve servise
  - Volumes za perzistenciju podataka
  - Health checks za sve servise
  
- [ ] **Koordinacija timova:**
  - Code review za Pull Requestove
  - Merge koordinacija
  - Rješavanje merge conflicta
  - Testiranje integracije nakon svakog merge-a
  
- [ ] **Tehnička dokumentacija:**
  - `docs/ARCHITECTURE.md` - dijagram sustava, komponente, flow
  - `docs/SETUP.md` - kako pokrenuti projekt (prerequesites, koraci)
  - `docs/API.md` - dokumentacija svih endpointa (Central, BTS)
  - `docs/DEPLOYMENT.md` - deployment upute
  
- [ ] **Završna prezentacija:**
  - Pripremiti slides (5-10 min)
  - Live demo script
  - Screenshotovi Grafane
  - Video demo (backup ako live ne radi)

**Datoteke za dodati/modificirati:**
```
.
├── docker-compose.yml            (UPDATE - dodati sve servise)
└── docs/
    ├── ARCHITECTURE.md           (NOVO)
    ├── SETUP.md                  (NOVO)
    ├── API.md                    (NOVO)
    └── DEPLOYMENT.md             (NOVO)
```

---

### 7️⃣ Simulator & Frontend (Preddiplomski tim - 7 članova)

> **KRITIČAN PRIORITET** - Bez simulatora ne možemo testirati sustav! ⚠️

#### Tim 1: Komunikacija s BTS-ovima (Lukas Kraljić, Toni Kukec, Josip Mraković)

**Lukas Kraljić:**
- [ ] **REST client za BTS:**
  - POST /api/v1/connect implementacija
  - JSON payload: `{imei, timestamp, user_location: {x, y}}`
  - Error handling za network failures
  
- [ ] **IMEI generator:**
  - 15 znamenki (TAC + SNR + Luhn checksum)
  - Funkcija `generate_imei()` koja vraća valjan IMEI
  - Lista realnih TAC kodova (iz TACDB)
  
- [ ] **Testiranje na stvarnim BTS-ovima:**
  - Testirati sve 3 BTS instance
  - Verificirati da odgovori dolaze ispravno

**Toni Kukec:**
- [ ] **BTS discovery:**
  - GET zahtjev na sve poznate BTS health endpointe
  - Lista aktivnih BTS-ova s njihovim lokacijama
  - Funkcija `discover_bts()` -> List[{bts_id, location}]
  
- [ ] **Nearest BTS selection:**
  - Kalkulacija Euclidean distance do svih BTS-ova
  - Odabir najbližeg BTS-a za korisnikovu lokaciju
  - Funkcija `select_nearest_bts(user_location)`
  
- [ ] **Handover logika:**
  - Ako BTS vrati `{action: "handover", target_bts_id}`, prebaci korisnika
  - Update korisničke lokacije i slanje zahtjeva na novi BTS

**Josip Mraković:**
- [ ] **HMAC integration (Simulator strana):**
  - Integracija s `security/hmac_utils.py`
  - Dodavanje X-HMAC-Signature headera u sve zahtjeve
  - Koordinacija sa Security timom
  
- [ ] **Retry logic:**
  - Exponential backoff za failed requests
  - Max 3 retrya
  - Logging svih grešaka
  
- [ ] **Logging i debugging:**
  - Python logging setup
  - Log svaki zahtjev i odgovor
  - Log file: `simulator.log`

#### Tim 2: Simulacija korisnika (Toni Kapučija, Vinko Šapina)

**Toni Kapučija:**
- [ ] **Generate funkcija:**
  - Parametri: `num_users`, `num_events`, `grid_size` (default 1000x1000)
  - Generira N korisnika koji se kreću random walk-om
  - Svaki korisnik ima svoj IMEI (generiraj na početku)
  - Spremanje scenario u CSV: `imei,timestamp,x,y`
  
- [ ] **Random walk algoritam:**
  - Korisnik počinje na random (x,y)
  - Svaki event: pomakni se +/- random step (npr. 10-50m)
  - Postavi timestamp (current_time + delta)
  - Povremeno miruj (50% šansa da ne pomakneš)
  
- [ ] **Flask backend:**
  - POST /generate endpoint
  - Accepts: `{num_users, num_events}`
  - Returns: CSV file za download

**Vinko Šapina:**
- [ ] **Replay funkcija:**
  - Parametar: CSV file path
  - Čita CSV red po red
  - Za svaki event, pošalji POST zahtjev na odgovarajući BTS
  - Progress tracking (koliko % je gotovo)
  
- [ ] **Testni scenariji:**
  - **Normalan:** korisnik se kreće normalnom brzinom
  - **Anomalan:** korisnik se kreće 300 km/h (trigger speed anomaly)
  - **Flapping:** korisnik se vraća između 2 BTS-a 10 puta (trigger flapping)
  - CSV fileovi za svaki scenarij
  
- [ ] **Flask backend:**
  - POST /replay endpoint
  - File upload support
  - Real-time progress updates (WebSocket ili SSE)

#### Tim 3: Frontend (Ante Boban, Luka Salopek)

**Ante Boban:**
- [ ] **React setup:**
  - Create React App ili Vite
  - Osnovni layout (header, main, footer)
  - Routing (home, generate, replay, connect)
  
- [ ] **Forma za Generate:**
  - Input fields: broj korisnika, broj događaja
  - Submit button
  - Prikaz rezultata (CSV preview)
  - Download button za CSV
  
- [ ] **Forma za Connect:**
  - Input: IMEI, X, Y koordinate
  - Submit šalje POST na Flask backend
  - Prikaz odgovora od BTS-a
  
- [ ] **Styling:**
  - Basic CSS ili Tailwind
  - Responsive design

**Luka Salopek:**
- [ ] **Forma za Replay:**
  - File upload input
  - Submit button
  - Progress bar (prikaz % completed)
  - Error handling i user feedback
  
- [ ] **Integracija s backendom:**
  - Axios ili fetch za HTTP requests
  - Error handling za network failures
  - Loading states
  
- [ ] **End-to-end testiranje:**
  - Testirati cijeli flow: Generate → Download → Replay
  - Verificirati da se podaci pojavljuju u Grafani
  - Bug fixing

**Datoteke za dodati:**
```
simulator/
├── src/
│   ├── bts_client.py          (NOVO - Lukas)
│   ├── imei_generator.py      (NOVO - Lukas)
│   ├── discovery.py           (NOVO - Toni K.)
│   ├── handover.py            (NOVO - Toni K.)
│   ├── generator.py           (NOVO - Toni Kap.)
│   ├── replay.py              (NOVO - Vinko)
│   └── app.py                 (NOVO - Flask backend)
├── frontend/
│   ├── src/
│   │   ├── App.jsx            (NOVO - Ante, Luka)
│   │   ├── components/
│   │   │   ├── GenerateForm.jsx
│   │   │   ├── ReplayForm.jsx
│   │   │   └── ConnectForm.jsx
│   └── package.json
├── tests/
│   └── scenarios/
│       ├── normal.csv
│       ├── speed_anomaly.csv
│       └── flapping.csv
├── requirements.txt
└── README.md
```

---

## 📋 Workflow

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

1. **Kloniraj repo i kreiraj branch:**
   ```bash
   git clone https://github.com/DIPPRO25-26/mobile-network-simulation.git
   cd mobile-network-simulation
   git checkout -b feature/your-feature-name
   ```

2. **Implementiraj feature** (vidi gornje zadatke za svoj tim)

3. **Testiraj lokalno** (ako je moguće)

4. **Commit s opisnom porukom:**
   ```bash
   git add .
   git commit -m "feat(central): add distance/speed calculation to CDR"
   ```

5. **Push na GitHub:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Otvori Pull Request:**
   - Idi na GitHub repo
   - Klikni "Compare & pull request"
   - Opiši što si napravio
   - Request review od kolege iz tima

7. **Code review i merge:**
   - Kolegica/kolega pregleda kod
   - Eventualno traži izmjene
   - Nakon approval, merge u main

---

## 🧪 Testiranje integracije

**Nakon što su osnovne komponente gotove:**

```bash
# 1. Pokreni sve servise
cd /path/to/mobile-network-simulation
docker-compose up -d

# 2. Provjeri da sve radi
curl http://localhost:8080/api/v1/user/health
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8083/health

# 3. Simuliraj korisnika (ručno - dok simulator nije gotov)
curl -X POST http://localhost:8081/api/v1/connect \
  -H "Content-Type: application/json" \
  -d '{"imei": "123456789012345", "timestamp": "2026-01-08T14:00:00Z", "user_location": {"x": 105, "y": 105}}'

# 4. Provjeri CDR zapise
docker exec mobile-network-db psql -U admin -d mobile_network \
  -c "SELECT * FROM cdr_records ORDER BY created_at DESC LIMIT 5;"

# 5. Provjeri Redis cache
docker exec mobile-network-redis redis-cli KEYS "*"

# 6. Otvori Grafanu
open http://localhost:3000  # username: admin, password: admin
```

---

## ❗ VAŽNO - KISS Princip

**Keep It Simple, Stupid!**

✅ **Radi:**
- Minimalni funkcionalitet koji zadovoljava zahtjeve
- Rule-based anomaly detection (bez ML)
- HMAC security (skip mTLS)
- 4 osnovna Grafana panela
- Jednostavna dokumentacija

❌ **Ne radi:**
- Kompleksni ML modeli
- Kubernetes orchestration
- Real-time streaming s Kafkom
- Mikroservisna arhitektura
- Mobile aplikacija
- Blockchain integracija 😂

---

## 📞 Komunikacija

- **Discord:** Dnevna komunikacija, update svaka 2-3 dana
- **GitHub Issues:** Za bugove i pitanja
- **Pull Requests:** Za code review
- **Sastanci:** Po potrebi (koordinira Roko)

---

## 📚 Resursi

- **GitHub Repo:** https://github.com/DIPPRO25-26/mobile-network-simulation
- **Plan projekta:** `docs/Prva verzija plana projekta.pdf`
- **Specifikacije:** `docs/Specifikacije_podtimovi_DIPL_projekt.pdf`
- **API Docs:** (bit će dodano u `docs/API.md`)

---

## ❓ Pitanja?

- **Discord kanal** - najbrza komunikacija
- **GitHub Issues** - za tehnička pitanja
- **Roko (projekt voditelj)** - za koordinaciju

---

**IDEMO! 💪 Svaki član zna što mora napraviti. Počnite sa svojim zadacima!**
