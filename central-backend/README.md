# Central Backend

Spring Boot servis koji služi kao centralni čvor za prikupljanje podataka od BTS stanica.

## Odgovornosti

- Prijem podataka o kretanju korisnika od BTS-ova
- Generiranje i pohranjivanje CDR zapisa
- Praćenje prethodnih lokacija korisnika
- Validacija HMAC potpisa zahtjeva
- Audit logging svih API poziva
- Izlaganje podataka za analitiku i vizualizaciju

## Tim

- **Ante Prkačin** - Voditelj, implementacija API-ja
- **Nikola Vlahović** - Dizajn baze i Spring Data repozitoriji
- **Leon Lakić** - Business logika i integracija

## Tehnologije

- Java 17+
- Spring Boot 3.x
- Spring Data JPA
- PostgreSQL
- Redis (za cache)
- Maven/Gradle

## API Endpoints

### POST /api/v1/user
Prima podatke o korisniku od BTS-a.

### GET /api/v1/cdr
Dohvaća CDR zapise s filterima.

### GET /api/v1/alerts
Dohvaća anomalije.

### GET /api/v1/health
Health check endpoint.

Detaljna API dokumentacija: [/docs/api/README.md](../docs/api/README.md)

## Database Schema

### Tablice:
- `cdr_records` - CDR zapisi
- `alerts` - Detekcije anomalija
- `user_activity` - Trenutno stanje korisnika
- `bts_registry` - Registar BTS stanica
- `audit_log` - Audit trail

Schema: [src/main/resources/schema.sql](src/main/resources/schema.sql)

## Razvojno okruženje

### Lokalni development (bez Dockera)

```bash
# Pokreni PostgreSQL i Redis
docker-compose up -d postgres redis

# Postavi environment varijable
export SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/mobile_network
export SPRING_DATASOURCE_USERNAME=admin
export SPRING_DATASOURCE_PASSWORD=admin123
export HMAC_SECRET_KEY=your-secret-key

# Build i run
./mvnw spring-boot:run
```

### Docker build

```bash
docker build -t central-backend:latest .
```

## Configuration

### application.properties

```properties
spring.datasource.url=${SPRING_DATASOURCE_URL}
spring.datasource.username=${SPRING_DATASOURCE_USERNAME}
spring.datasource.password=${SPRING_DATASOURCE_PASSWORD}

spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=false

spring.redis.host=${SPRING_REDIS_HOST:localhost}
spring.redis.port=${SPRING_REDIS_PORT:6379}

security.hmac.secret-key=${HMAC_SECRET_KEY}
security.hmac.timestamp-tolerance=300
```

## Security

Svi zahtjevi prema API-ju moraju sadržavati HMAC potpis u headerima:
- `X-HMAC-Signature` - HMAC-SHA256 potpis
- `X-Timestamp` - Unix timestamp

Implementacija HMAC validacije nalazi se u `security/HmacValidator.java`.

## Testing

```bash
# Unit testovi
./mvnw test

# Integration testovi
./mvnw verify
```

## Deployment

Servis se deploywa kao Docker container putem docker-compose.yml.

```bash
docker-compose up central-backend
```

## Faza 2 - Trenutni zadaci

- [ ] Implementacija POST /user endpointa
- [ ] Dizajn i kreiranje JPA entiteta (CDRRecord, Alert, UserActivity)
- [ ] Spring Data repozitoriji
- [ ] Business logika za pohranu CDR zapisa
- [ ] Vraćanje prethodne lokacije korisnika
- [ ] HMAC validacija middleware

**Deadline:** 20.11.2025
