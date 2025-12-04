# Rapporte - Support Stundenrapport Webapp

Kleine lokale Webapp zur Erfassung von Support-Stundenrapporten für IT-Dienstleistungen.

## Features

- **Kundenverwaltung**: Erfassung von Kundendaten, Kontaktinformationen und IT-Infrastruktur
- **Login-Daten**: Sichere Speicherung von Zugangsdaten für Kundengeräte (Computer, Router, Drucker, etc.)
- **Rapport-Erfassung**: Dokumentation von Support-Ereignissen mit Datum, Dauer, Thema und Kosten
- **Zahlungsverfolgung**: Unterscheidung zwischen Bar- und Rechnungszahlung
- **Kompakte Lösung**: Alles in einem Docker-Container mit SQLite-Datenbank

## Technologie

- **Backend**: Python 3.11 + Flask
- **Datenbank**: SQLite (persistent im `data/` Verzeichnis)
- **Frontend**: HTML/CSS (kein externes Framework)
- **Deployment**: Docker + Docker Compose

## Installation und Start

### Voraussetzungen
- Docker und Docker Compose installiert

### Starten
```bash
docker-compose up --build
```

Die Webapp ist dann unter **http://localhost:8085** erreichbar.

### Stoppen
```bash
docker-compose down
```

## Daten

Die SQLite-Datenbank wird im `data/` Verzeichnis gespeichert und bleibt auch nach Container-Neustarts erhalten.

## Entwicklung

Ohne Docker lokal ausführen:
```bash
pip install -r requirements.txt
export DATABASE_PATH=./data/rapporte.db
python -m flask --app app.main run --debug --port 8085
```

## Datenbank-Administration

### Direkt auf die Datenbank zugreifen
Die SQLite-Datenbank liegt unter `./data/rapporte.db` und kann direkt mit `sqlite3` bearbeitet werden:

```bash
# Auf die Datenbank zugreifen
sqlite3 ./data/rapporte.db

# Hilfreiche SQLite-Befehle:
.tables                    # Alle Tabellen anzeigen
.schema kunden            # Schema einer Tabelle anzeigen
SELECT * FROM kunden;     # Daten abfragen
.quit                     # SQLite beenden
```

### Alle Daten löschen (Tabellen bleiben erhalten)
```bash
# Alle Rapporte löschen
sqlite3 ./data/rapporte.db "DELETE FROM rapporte;"

# Alle Login-Daten löschen
sqlite3 ./data/rapporte.db "DELETE FROM login_daten;"

# Alle Kunden löschen
sqlite3 ./data/rapporte.db "DELETE FROM kunden;"

# ALLES auf einmal löschen
sqlite3 ./data/rapporte.db "DELETE FROM rapporte; DELETE FROM login_daten; DELETE FROM kunden;"
```

### Datenbank komplett neu erstellen
```bash
# Stoppe den Container
docker-compose down

# Lösche die Datenbankdatei
rm ./data/rapporte.db

# Starte den Container neu (DB wird automatisch neu erstellt)
docker-compose up -d
```

### Backup erstellen
```bash
# Einfaches Backup
cp ./data/rapporte.db ./data/rapporte_backup_$(date +%Y%m%d).db

# Oder mit sqlite3
sqlite3 ./data/rapporte.db ".backup ./data/rapporte_backup_$(date +%Y%m%d).db"
```

### Backup wiederherstellen
```bash
# Stoppe den Container
docker-compose down

# Ersetze die aktuelle DB mit dem Backup
cp ./data/rapporte_backup_20241204.db ./data/rapporte.db

# Starte den Container neu
docker-compose up -d
```
