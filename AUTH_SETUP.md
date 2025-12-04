# HTTP Basic Auth Setup

Die App ist mit HTTP Basic Auth geschützt. 

## Passwort einrichten

1. Generiere einen Passwort-Hash:
```bash
python3 generate_password.py "dein_sicheres_passwort"
```

2. Kopiere den Hash und füge ihn in `docker-compose.yml` ein:
```yaml
environment:
  - AUTH_USERNAME=admin  # Dein Username
  - AUTH_PASSWORD_HASH=scrypt:32768:8:1$...  # Der generierte Hash
```

3. Container neu starten:
```bash
docker compose down
docker compose up -d
```

## Standard-Login (UNSICHER - bitte ändern!)
- Username: `admin`
- Passwort: `changeme`

**WICHTIG**: Ändere das Passwort sofort nach dem ersten Start!
