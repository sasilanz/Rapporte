# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

German-language Flask web application for tracking IT support hours (Stundenrapporte). Manages customers, their login credentials, and support session reports with payment tracking.

## Tech Stack

- Python 3.11 + Flask
- SQLite database (persistent in `data/rapporte.db`)
- Docker deployment
- HTTP Basic Auth (Flask-HTTPAuth + Werkzeug)
- ReportLab for PDF export

## Common Commands

### Docker (Production)
```bash
docker-compose up --build      # Build and start
docker-compose down            # Stop
```

### Local Development
```bash
pip install -r requirements.txt
export DATABASE_PATH=./data/rapporte.db
python -m flask --app app.main run --debug --port 8085
```

Access at http://localhost:8085 (default: admin/changeme)

### Test Data
```bash
python insert_test_data.py
```

### Password Management
```bash
python3 generate_password.py "new_password"  # Generate hash for docker-compose.yml
```

## Architecture

```
app/
├── main.py          # Flask routes, auth, business logic (~395 lines)
├── database.py      # SQLite schema and connection (dict row factory)
└── templates/       # Jinja2 templates with embedded CSS
    ├── base.html    # Master template with navigation and styles
    └── ...          # Feature-specific templates
```

### Database Schema (3 tables)
- **kunden**: Customers (name, email, telefon, adresse, it_infrastruktur, stundensatz)
- **login_daten**: Device credentials per customer (geraet_typ, username, passwort)
- **rapporte**: Support reports (datum, dauer_minuten, thema, kosten, bezahlt, zahlungsart)

### Key Patterns
- All routes protected with `@auth.login_required`
- Custom Jinja filter `date_ch` converts dates to Swiss format (DD.MM.YYYY)
- Cost auto-calculated from duration × hourly rate (default 120 CHF/hour)
- Parameterized SQL queries for injection prevention
- Auth credentials via environment variables (AUTH_USERNAME, AUTH_PASSWORD_HASH)

## Language

All UI, comments, and variable names are in German.
