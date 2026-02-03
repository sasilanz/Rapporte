#!/usr/bin/env python3
"""
Migriert bestehende Adressen (Freitext) in separate Felder.
Einmalig nach Schema-Update ausführen!
"""
import sqlite3
import re

def parse_adresse(adresse_text):
    """Versucht Adresse in Komponenten zu zerlegen"""
    if not adresse_text:
        return None, None, None, None

    lines = [l.strip() for l in adresse_text.strip().split('\n') if l.strip()]

    strasse = None
    hausnummer = None
    plz = None
    stadt = None

    # Erste Zeile: Strasse + Hausnummer
    if len(lines) >= 1:
        # Trenne Hausnummer am Ende ab (Zahlen oder Zahlen+Buchstabe)
        match = re.match(r'^(.+?)\s+(\d+[a-zA-Z]?)$', lines[0])
        if match:
            strasse = match.group(1).strip()
            hausnummer = match.group(2).strip()
        else:
            strasse = lines[0]

    # Letzte Zeile: PLZ + Stadt
    if len(lines) >= 2:
        last_line = lines[-1]
        match = re.match(r'^(\d{4})\s+(.+)$', last_line)
        if match:
            plz = match.group(1)
            stadt = match.group(2).strip()

    return strasse, hausnummer, plz, stadt

def migrate_addresses(db_path='data/rapporte.db'):
    """Führt Migration durch"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=== Schema-Update ===")

    # 1. Prüfe ob neue Spalten existieren, füge sie hinzu falls nicht
    cursor.execute("PRAGMA table_info(kunden)")
    columns = [col[1] for col in cursor.fetchall()]

    new_columns = ['strasse', 'hausnummer', 'plz', 'stadt']
    for col in new_columns:
        if col not in columns:
            print(f"  Füge Spalte '{col}' zur kunden-Tabelle hinzu...")
            cursor.execute(f"ALTER TABLE kunden ADD COLUMN {col} TEXT")
        else:
            print(f"  Spalte '{col}' existiert bereits ✓")

    # 2. Erstelle rechnungen-Tabelle falls nicht vorhanden
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rechnungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rechnungs_nummer TEXT UNIQUE NOT NULL,
            kunde_id INTEGER NOT NULL,
            erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            betrag REAL NOT NULL,
            rapport_ids TEXT NOT NULL,
            FOREIGN KEY (kunde_id) REFERENCES kunden (id)
        )
    ''')
    print("  rechnungen-Tabelle geprüft/erstellt ✓")

    conn.commit()
    print("\n=== Daten-Migration ===")

    # Hole alle Kunden mit adresse
    kunden = cursor.execute('SELECT id, name, adresse FROM kunden').fetchall()

    print(f"Migriere {len(kunden)} Kunden...")

    for kunde in kunden:
        if not kunde['adresse']:
            print(f"  Kunde {kunde['id']} ({kunde['name']}): Keine Adresse")
            continue

        strasse, hausnr, plz, stadt = parse_adresse(kunde['adresse'])

        print(f"  Kunde {kunde['id']} ({kunde['name']}):")
        print(f"    Original: {kunde['adresse']}")
        print(f"    Geparst: {strasse} {hausnr}, {plz} {stadt}")

        # Update
        cursor.execute('''
            UPDATE kunden
            SET strasse=?, hausnummer=?, plz=?, stadt=?
            WHERE id=?
        ''', (strasse, hausnr, plz, stadt, kunde['id']))

    conn.commit()
    conn.close()
    print("\nMigration abgeschlossen!")

if __name__ == '__main__':
    migrate_addresses()
