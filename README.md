# Simulacija mobilne mreže s detekcijom anomalija

## 📋 Opis projekta

Distribuirani sustav koji simulira rad mobilne mreže sastavljene od više baznih stanica (BTS) implementiranih pomoću Docker kontejnera. Sustav prikuplja CDR (Call Detail Record) zapise i provodi lokalnu i centralnu detekciju anomalija.

## 🏗️ Arhitektura

```
┌─────────────────────┐
│  Anomaly Identifier │
└──────────┬──────────┘
           │
    ┌──────▼──────┐         ┌──────────┐
    │   Central   │◄────────┤ Database │
    │    Node     │         │PostgreSQL│
    └──┬───┬───┬──┘         └──────────┘
       │   │   │
    ┌──▼┐ ┌▼─┐ ┌▼──┐
    │BTS│ │BTS│ │BTS│
    └─┬─┘ └─┬┘ └─┬─┘
      │     │    │
   ┌──▼─────▼────▼──┐
   │   Simulator    │
   └────────────────┘
```

### Komponente:

- **Central Backend** - Spring Boot servis za prikupljanje podataka, generiranje CDR zapisa
- **BTS Servisi** - Lokalni servisi baznih stanica s Redis cache-om
- **Analytics** - Python modul za detekciju anomalija (lokalno i centralno)
- **Visualization** - Grafana dashboardi za prikaz prometa i anomalija
- **Security** - HMAC autentifikacija, mTLS, audit log
- **Simulator** - Generator događaja kretanja korisnika

## 🗂️ Struktura projekta

```
mobile-network-simulation/
├── central-backend/          # Spring Boot centralni servis
│   ├── src/main/java/fer/project/central/
│   │   ├── controller/       # REST API endpoints
│   │   ├── service/          # Business logika
│   │   ├── model/            # JPA entiteti (CDR, Alert, Activity)
│   │   ├── repository/       # Spring Data repozitoriji
│   │   ├── security/         # HMAC validacija
│   │   └── config/           # Konfiguracija
│   └── src/main/resources/   # application.properties, schema.sql
│
├── bts-service/              # BTS servis (Java/Python/Go)
│   ├── src/                  # Izvorni kod
│   ├── config/               # Konfiguracija BTS-a
│   └── cache/                # Redis cache setup
│
├── analytics/                # Python modul za analitiku
│   ├── src/
│   │   ├── anomaly_detection/ # Algoritmi detekcije
│   │   └── metrics/          # Računanje metrika
│   ├── notebooks/            # Jupyter notebooks za analizu
│   └── models/               # ML modeli (ako se koriste)
│
├── visualization/            # Grafana setup
│   ├── dashboards/           # JSON definicije dashboarda
│   └── datasources/          # Konfiguracija izvora podataka
│
├── security/                 # Sigurnosni sloj
│   ├── certs/                # mTLS certifikati
│   ├── keys/                 # HMAC ključevi
│   └── audit/                # Audit log konfiguracija
│
├── simulator/                # Simulator korisnika (preddiplomski tim)
│   ├── backend/              # Flask/FastAPI backend
│   └── frontend/             # React frontend
│
├── scripts/                  # Pomocni skripte
│   ├── init-db.sh           # Inicijalizacija baze
│   ├── generate-certs.sh    # Generiranje certifikata
│   └── seed-data.sh         # Test podaci
│
├── docs/                     # Dokumentacija
│   ├── api/                  # API specifikacije
│   ├── architecture/         # Arhitekturni dijagrami
│   └── setup/                # Setup upute
│
├── .github/workflows/        # CI/CD
│
├── docker-compose.yml        # Orkestracija svih servisa
├── docker-compose.dev.yml    # Development override
└── README.md
```

## 🔑 Ključni podaci

### CDR Zapis
```json
{
  "imei": "123456789012345",
  "mcc": "219",
  "mnc": "01",
  "lac": "1001",
  "bts_id": "BTS001",
  "previous_bts_id": "BTS002",
  "timestamp_arrival": "2025-01-08T10:30:00Z",
  "timestamp_departure": "2025-01-08T10:35:00Z",
  "user_location": {"x": 100, "y": 200},
  "distance": 150.5,
  "speed": 30.1,
  "duration": 300
}
```

### Lokacija ćelije
Kombinacija `(MCC, MNC, LAC, BTS_ID)` čini jedinstvenu lokaciju ćelije:
- **MCC** - Mobile Country Code (219 za Hrvatsku)
- **MNC** - Mobile Network Code (01, 02, 10...)
- **LAC** - Location Area Code (grupa ćelija)
- **BTS_ID** - Identifikator bazne stanice

## 🚀 Brzi start

### Preduvjeti
- Docker & Docker Compose
- Java 17+ (za development)
- Python 3.9+ (za analytics)
- Node.js 18+ (za frontend)

### Pokretanje

```bash
# 1. Kloniraj repozitorij
git clone <repo-url>
cd mobile-network-simulation

# 2. Kopiraj env template i postavi varijable
cp .env.example .env

# 3. Generiraj certifikate (za mTLS)
./scripts/generate-certs.sh

# 4. Pokreni cijeli sustav
docker-compose up -d

# 5. Inicijaliziraj bazu
./scripts/init-db.sh

# 6. Provjeri status
docker-compose ps
```

### Pristup servisima

- **Central API**: http://localhost:8080
- **Grafana**: http://localhost:3000 (admin/admin)
- **Simulator UI**: http://localhost:5000
- **PostgreSQL**: localhost:5432

## 📊 Faze projekta

- [x] **Faza 0**: Formiranje tima (1.10 - 10.10)
- [x] **Faza 1**: Definicija specifikacija (11.10 - 05.11)
- [ ] **Faza 2**: Razvoj minimalnog sustava (05.11 - 20.11) ⬅️ **TRENUTNO**
- [ ] **Faza 3**: Integracija i proširenje (20.11 - 10.12)
- [ ] **Faza 4**: Napredne značajke (10.12 - 20.12)
- [ ] **Faza 5**: Testiranje i dokumentacija (21.12 - 20.01)
- [ ] **Faza 6**: Prezentacija (20.01 - 30.01)

## 👥 Tim

**Diplomski projekt:**
- **Voditelj**: Roko Gligora
- **Central Backend**: Ante Prkačin, Nikola Vlahović, Leon Lakić
- **BTS Servisi**: Matija Alojz Stuhne, Nikola Vlahović
- **Analitika**: Nikola Petrović, Jurica Galić
- **Vizualizacija**: Jurica Galić, Nikola Petrović
- **Sigurnost**: Jana Bulum, Ivan Đurić

**Preddiplomski projekt (Simulator):**
- Lukas Kraljić, Toni Kukec, Josip Mrakovčić
- Toni Kapučija, Vinko Šapina
- Ante Boban, Luka Salopek

## 📚 Dokumentacija

- [API specifikacija](docs/api/README.md)
- [Arhitektura sustava](docs/architecture/README.md)
- [Setup i deployment](docs/setup/README.md)
- [Security mehanizmi](security/README.md)

## 📝 Licenca

FER - Projekt © 2026
