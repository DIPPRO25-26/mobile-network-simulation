# Contributing Guidelines

Upute za sve članove tima kako doprinositi projektu.

## 🔧 Setup razvojnog okruženja

### 1. Kloniraj repozitorij

```bash
git clone https://github.com/DIPPRO25-26/mobile-network-simulation.git
cd mobile-network-simulation
```

### 2. Konfiguriraj Git

```bash
git config user.name "Tvoje Ime"
git config user.email "tvoj.email@fer.hr"
```

### 3. Kopiraj .env template

```bash
cp .env.example .env
```

### 4. Generiraj certifikate (za security)

```bash
./scripts/generate-certs.sh
```

### 5. Pokreni razvojno okruženje

```bash
# Pokreni samo bazu i Redis za lokalni development
docker-compose up -d postgres redis

# Ili pokreni cijeli sustav
docker-compose up -d
```

## 🌿 Git Workflow

### Branch strategija

- `main` - glavna grana, uvijek stabilna
- `dev` - razvojna grana za integraciju
- `feature/<ime-featurea>` - grane za nove značajke
- `fix/<ime-fixa>` - grane za bugfixeve

### Kreiranje nove grane

```bash
# Uvijek kreni od najnovijeg maina
git checkout main
git pull origin main

# Kreiraj novu granu
git checkout -b feature/central-backend-api
```

### Commit poruke

Format commit poruke:

```
<type>: <kratki opis>

<dulji opis - opcijski>

Co-Authored-By: Warp <agent@warp.dev>
```

**Types:**
- `feat:` - nova značajka
- `fix:` - ispravak greške
- `docs:` - dokumentacija
- `style:` - formatiranje koda
- `refactor:` - refactoring
- `test:` - dodavanje testova
- `chore:` - build/config promjene

**Primjeri:**
```bash
git commit -m "feat: implement POST /user endpoint"

git commit -m "fix: resolve HMAC validation issue" -m "Fixed timestamp tolerance check in HmacValidator"

git commit -m "docs: add API documentation for /cdr endpoint"
```

### Pull Requests

1. Push-aj svoju granu na GitHub:
```bash
git push -u origin feature/central-backend-api
```

2. Otvori Pull Request na GitHubu
3. Dodaj opis što PR rješava
4. Zatraži review od članova tima
5. Označi povezane issue-e (ako postoje)

**PR naslov format:**
```
[Component] Kratak opis

Primjer: [Central Backend] Implement POST /user endpoint
```

**PR opis template:**
```markdown
## Opis
Kratki opis što PR rješava.

## Promjene
- Lista glavnih promjena
- Novi endpointi / funkcionalnosti
- Breaking changes (ako ih ima)

## Testing
Kako testirati promjene.

## Checklist
- [ ] Kod je testiran lokalno
- [ ] Dodani unit testovi
- [ ] Dokumentacija ažurirana
- [ ] Nema merge konflikata
```

## 📁 Struktura projekta i vlasništvo

Svaki podtim radi na svojoj komponenti:

- **central-backend/** → Ante, Nikola V., Leon
- **bts-service/** → Matija, Nikola V.
- **analytics/** → Nikola P., Jurica
- **visualization/** → Jurica, Nikola P.
- **security/** → Jana, Ivan
- **simulator/** → Preddiplomski tim

## 🔍 Code Review

Svaki PR treba review od **najmanje jednog člana tima** prije merganja.

**Što provjeriti u reviewu:**
- [ ] Kod je čitljiv i održiv
- [ ] Slijedi postojeće konvencije projekta
- [ ] Nema hardkodiranih secretsa
- [ ] Testovi prolaze
- [ ] Dokumentacija je ažurirana

## 🧪 Testing

### Prije commit-a

```bash
# Java/Spring Boot
./mvnw test

# Python
pytest

# JavaScript/Node
npm test
```

### Integration testovi

```bash
# Pokreni cijeli sustav
docker-compose up -d

# Testiraj endpoint
curl http://localhost:8080/api/v1/health
```

## 📝 Dokumentacija

Kada dodaješ novi feature:

1. **README.md** - ažuriraj component README
2. **API docs** - dodaj u `docs/api/README.md`
3. **Code comments** - komplicirane funkcije trebaju komentare
4. **Inline docs** - JavaDoc, Python docstrings, JSDoc

## 🚫 Što NE smije u Git

**NIKAD ne commitaj:**
- ❌ `.env` datoteke
- ❌ Private keys / certifikate (`security/keys/`, `security/certs/`)
- ❌ Lozinke, API ključeve
- ❌ IDE konfiguraciju (`.idea/`, `.vscode/`)
- ❌ Build artifakte (`target/`, `node_modules/`)
- ❌ Log datoteke

Sve je to pokriveno u `.gitignore`, ali dvaput provjeri!

## 🐛 Pronašao si bug?

1. Provjeri postoji li već issue na GitHubu
2. Ako ne, otvori novi issue s:
   - Naslovom koji opisuje problem
   - Koracima za reproduciranje
   - Očekivanim vs. stvarnim ponašanjem
   - Logovima / screenshotima
3. Označi s odgovarajućim label-om (bug, enhancement, question)

## 💬 Komunikacija

- **Discord** - dnevna komunikacija
- **GitHub Issues** - praćenje zadataka
- **GitHub Discussions** - diskusije o dizajnu
- **Tjedni sastanci** - update mentorima

## 🎯 Faza 2 - Prioriteti (05.11 - 20.11)

Svaki podtim se fokusira na svoj MVP:

### Central Backend
- POST /user endpoint
- Pohrana CDR zapisa
- Vraćanje prethodne lokacije

### BTS Servisi
- POST /connect endpoint
- Redis cache
- Slanje podataka Centralu

### Security
- HMAC potpis
- Timestamp validacija

### Analitika
- Pipeline za dohvat podataka
- Definiranje značajki

## ❓ Pitanja?

- Pitaj na Discord kanalu
- Otvori GitHub Discussion
- Obrati se voditelju svog podtima
- Obrati se voditelju projekta (Roko)

---

**Važno:** Projekt je timski rad. Komunicirajmo otvoreno, pomažimo jedni drugima i držimo se rokova! 🚀
