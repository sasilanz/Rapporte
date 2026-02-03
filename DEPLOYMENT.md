# Deployment-Anleitung: Rapporte

## Lokale Entwicklung (DEV)

```bash
# 1. .env File erstellen (falls nicht vorhanden)
cp .env.example .env
# Dann .env mit echten Daten füllen

# 2. Container starten (ohne externes Netzwerk)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# 3. Logs checken
docker-compose logs -f rapporte-app

# 4. App öffnen
# http://localhost:8085
```

## Production Deployment

### **Erstmaliges Setup auf Prod-Server**

```bash
# 1. Git Repository klonen/pullen
cd /pfad/zum/deployment
git pull origin main

# 2. .env File erstellen (WICHTIG: Nicht aus Git!)
cp .env.example .env
nano .env  # Mit echten Produktions-Daten füllen

# 3. Datenbank von Dev kopieren (einmalig bei Migration)
scp user@dev-server:/home/asiend/dev/Rapporte/data/rapporte.db ./data/

# 4. Container starten (MIT dieti-it Netzwerk)
docker-compose up --build -d

# 5. Logs checken
docker-compose logs -f rapporte-app

# 6. Testen
curl http://localhost:8085
```

### **Updates auf Prod deployen**

```bash
# 1. Git pullen
git pull origin main

# 2. Container neu bauen
docker-compose up --build -d

# 3. Logs checken
docker-compose logs -f rapporte-app
```

## Datenbank-Migration

Falls Schema-Änderungen vorhanden:

```bash
# 1. Backup erstellen
cp data/rapporte.db data/rapporte_backup_$(date +%Y%m%d_%H%M%S).db

# 2. Migration ausführen (falls nötig)
python3 migrate_adressen.py

# 3. Container neu starten
docker-compose restart rapporte-app
```

## Wichtige Dateien

- `.env` - **NIEMALS committen!** Enthält sensitive Daten (IBAN, Passwörter)
- `.env.example` - Template für .env (KANN committet werden)
- `docker-compose.yml` - Prod-Config (mit dieti-it Netzwerk)
- `docker-compose.dev.yml` - Dev-Overrides (ohne Netzwerk)
- `data/*.db` - Datenbanken (**NICHT committen!**)

## Netzwerk-Info

- **DEV**: Läuft standalone ohne externes Netzwerk
- **PROD**: Nutzt `dieti-it` Netzwerk (muss bereits existieren via Dietipi-App)

Falls Dietipi-App noch nicht läuft:
```bash
cd /pfad/zu/dietipi-app
docker-compose up -d  # Erstellt dieti-it Netzwerk
```
