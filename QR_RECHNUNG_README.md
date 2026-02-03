# Swiss QR Bill Rechnungsfunktion - Implementierung

## ✅ Implementierte Features

Die Swiss QR Bill Rechnungsfunktion wurde erfolgreich implementiert:

1. ✅ **Dependencies hinzugefügt** (`qrbill==1.2.0`, `svglib==1.5.1`)
2. ✅ **Datenbank-Schema erweitert**:
   - Kunden-Tabelle: Separate Adressfelder (strasse, hausnummer, plz, stadt)
   - Neue `rechnungen` Tabelle für Rechnungs-Tracking
3. ✅ **Migrations-Script erstellt** (`migrate_adressen.py`)
4. ✅ **QR-Bill-Funktionalität**:
   - Rechnungsnummer-Generierung (RE-YYYYMMDD-XXXXX)
   - QR-Code-Generierung mit Swiss QR Bill Standard
   - PDF-Rechnung mit QR-Code
5. ✅ **UI-Integration**: Rechnung-Button in Rapporte-Tabelle
6. ✅ **Kunden-Formulare**: Separate Adressfelder

## 📋 Nächste Schritte vor dem Deployment

### 1. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 2. Datenbank-Migration durchführen (falls bestehende Daten vorhanden)

**WICHTIG: Nur ausführen wenn bereits Kundendaten existieren!**

```bash
# Migration ausführen
python3 migrate_adressen.py

# Ergebnis prüfen
# Falls Docker läuft:
docker exec -it rapporte-web-1 sqlite3 /app/data/rapporte.db
sqlite> SELECT id, name, strasse, hausnummer, plz, stadt FROM kunden LIMIT 5;
sqlite> .exit
```

### 3. Environment-Variablen konfigurieren

Bearbeiten Sie `docker-compose.yml` und ersetzen Sie die Platzhalter mit Ihren echten Daten:

```yaml
environment:
  # ... bestehende Variablen ...
  - PAYEE_LEGAL_NAME=Ihr Name oder Firmenname
  - PAYEE_IBAN=CH5800791123000889012  # Ihre QR-IBAN
  - PAYEE_BANK=Name Ihrer Bank
  - PAYEE_BIC=POFICHBEXXX
  - PAYEE_DISPLAY_NAME=Ihr Anzeigename
  - PAYEE_ADDRESS_LINE1=Musterstrasse 123
  - PAYEE_ADDRESS_LINE2=8000 Zürich
  - PAYEE_COUNTRY=CH
```

**Tipp**: Kopieren Sie die Daten aus Ihrer Dietipi-App (`~/dev/Dietipi-App/.env`)

### 4. Docker Container neu starten

```bash
docker-compose down
docker-compose up --build -d
```

### 5. Testen

1. App öffnen: http://localhost:8085 (Login: admin/changeme)
2. Einen Rapport mit Kosten > 0 auswählen
3. "📄 Rechnung" Button klicken
4. PDF sollte heruntergeladen werden
5. QR-Code mit Banking-App scannen und prüfen:
   - IBAN korrekt?
   - Betrag korrekt?
   - Empfänger korrekt?
   - Rechnungsnummer in Mitteilung?

## 🔍 Funktionsweise

### Rechnungsnummer-Format
- Format: `RE-YYYYMMDD-XXXXX`
- Beispiel: `RE-20260203-00001`
- Automatische Sequenznummer pro Tag

### QR-Code Details
- **Standard**: Swiss QR Bill (ISO 20022)
- **Typ**: QR-IBAN ohne QRR-Referenz
- **Mitteilungsfeld**: Rechnungsnummer
- **Debtor-Daten**: Optional (falls Kundenadresse vorhanden)

### Datenbank-Tracking
Jede generierte Rechnung wird in der `rechnungen` Tabelle gespeichert:
- Rechnungsnummer (eindeutig)
- Kunde-ID
- Betrag
- Rapport-IDs (Komma-getrennt für Multi-Rapport später)
- Erstellungsdatum

## 🚀 Neue Features (optional für später)

Nach erfolgreichem MVP können folgende Features hinzugefügt werden:

1. **Multi-Rapport-Rechnungen**: Mehrere Rapporte auf einer Rechnung
2. **Rechnungs-Liste**: `/rechnungen` Route mit Übersicht
3. **Nachdrucken**: Bestehende Rechnungen erneut generieren
4. **E-Mail-Versand**: Rechnung direkt an Kunde mailen
5. **MwSt-Berechnung**: Falls MwSt-pflichtig
6. **Zahlungs-Tracking**: Bezahlt-Status mit Rechnung verknüpfen

## 📁 Geänderte Dateien

- `requirements.txt` - Dependencies
- `app/database.py` - Schema-Erweiterung
- `app/main.py` - QR-Bill-Logik und Route
- `app/templates/kunde_form.html` - Separate Adressfelder
- `app/templates/index.html` - Rechnung-Button
- `docker-compose.yml` - Environment-Variablen (kommentiert)
- `migrate_adressen.py` - Migrations-Script (neu)

## ⚠️ Wichtige Hinweise

- **QR-IBAN erforderlich**: Normale IBAN funktioniert nicht für QR-Rechnungen
- **Adress-Format**: Kunde muss PLZ und Stadt haben für korrekten QR-Code
- **PDF-Grösse**: QR-Code wird auf passende Grösse skaliert
- **Fehlerbehandlung**: Bei QR-Generierungs-Fehler wird Fehlermeldung im PDF angezeigt
- **Rapport-Text**: Das `thema`-Feld wird als Beschreibung auf der Rechnung angezeigt

## 🐛 Troubleshooting

### QR-Code wird nicht angezeigt
- Prüfen Sie, ob alle PAYEE_* Variablen gesetzt sind
- Prüfen Sie die Logs: `docker-compose logs -f web`

### "IBAN nicht konfiguriert" Fehler
- PAYEE_IBAN in docker-compose.yml setzen
- Container neu starten

### Migration-Script findet keine Datenbank
- Pfad in `migrate_adressen.py` anpassen (Zeile 58)
- Oder: Docker-Container-Pfad verwenden

### QR-Code scannt nicht
- Prüfen Sie IBAN-Format (QR-IBAN erforderlich)
- Prüfen Sie Adress-Format (PLZ muss 4-stellig sein)
- Versuchen Sie verschiedene Banking-Apps

## 📞 Support

Bei Fragen oder Problemen, siehe Implementierungsplan in der Conversation History.
