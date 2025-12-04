#!/usr/bin/env python3
"""Fügt Stundensatz-Feld zur Kunden-Tabelle hinzu"""
import sqlite3

db_path = './data/rapporte.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Füge stundensatz Spalte hinzu (Standard: 120 CHF/h)
    cursor.execute('ALTER TABLE kunden ADD COLUMN stundensatz REAL DEFAULT 120.0')
    conn.commit()
    print("✅ Stundensatz-Feld erfolgreich hinzugefügt!")
    print("   Standard: CHF 120.00/h")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("ℹ️  Stundensatz-Feld existiert bereits")
    else:
        print(f"❌ Fehler: {e}")

conn.close()
