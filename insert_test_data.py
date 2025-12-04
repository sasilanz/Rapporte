#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta
import random

# Verbinde zur Datenbank
db_path = './data/rapporte.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Testdaten: Kunden
kunden = [
    ('Müller AG', 'info@mueller-ag.ch', '044 123 45 67', 'Bahnhofstrasse 10, 8001 Zürich', 'MacBook Pro 2021, iPhone 13, FRITZ!Box 7590'),
    ('Schneider GmbH', 'kontakt@schneider.ch', '031 987 65 43', 'Bundesplatz 5, 3011 Bern', 'Windows 11 PC, HP LaserJet, Synology NAS'),
    ('Weber IT Solutions', 'office@weber-it.ch', '061 555 77 88', 'Centralbahnstrasse 20, 4051 Basel', 'Linux Server (Ubuntu), Dell Laptop, Brother Drucker'),
    ('Meier Consulting', 'meier@consulting.ch', '022 444 33 22', 'Rue du Mont-Blanc 15, 1201 Genf', 'MacBook Air M2, iPad Pro, AVM Router'),
]

print("Füge Kunden ein...")
kunde_ids = []
for kunde in kunden:
    cursor.execute(
        'INSERT INTO kunden (name, email, telefon, adresse, it_infrastruktur) VALUES (?, ?, ?, ?, ?)',
        kunde
    )
    kunde_ids.append(cursor.lastrowid)
    print(f"  ✓ {kunde[0]}")

# Testdaten: Login-Daten
print("\nFüge Login-Daten ein...")
logins = [
    (kunde_ids[0], 'Computer', 'MacBook Pro 2021', 'mueller_admin', 'Welcome2023!'),
    (kunde_ids[0], 'Router', 'FRITZ!Box 7590', 'admin', 'Fritz123Router'),
    (kunde_ids[1], 'Computer', 'Windows 11 Desktop', 'schneider', 'Schne1der$PC'),
    (kunde_ids[1], 'Drucker', 'HP LaserJet Pro', 'admin', 'hp1234'),
    (kunde_ids[1], 'NAS', 'Synology DS220+', 'administrator', 'NAS_Secure99'),
    (kunde_ids[2], 'Server', 'Ubuntu Server 22.04', 'root', 'Weber!Server2024'),
    (kunde_ids[3], 'Computer', 'MacBook Air M2', 'meier', 'Consult!ng123'),
    (kunde_ids[3], 'Router', 'AVM FRITZ!Box', 'admin', 'Router_2024'),
]

for login in logins:
    cursor.execute(
        'INSERT INTO login_daten (kunde_id, geraet_typ, beschreibung, username, passwort) VALUES (?, ?, ?, ?, ?)',
        login
    )
print(f"  ✓ {len(logins)} Login-Einträge hinzugefügt")

# Testdaten: Rapporte (letzte 30 Tage)
print("\nFüge Rapporte ein...")
themen = [
    'Email-Konfiguration Outlook',
    'WLAN-Problem behoben',
    'Drucker Installation und Einrichtung',
    'Backup-System konfiguriert',
    'Virus entfernt und System gesichert',
    'Software-Update durchgeführt',
    'Netzwerk-Kabel verlegt',
    'Passwort zurückgesetzt',
    'VPN-Zugang eingerichtet',
    'Festplatte ersetzt',
    'Bildschirm Installation',
    'Cloud-Backup eingerichtet',
    'Router neu konfiguriert',
    'Datenmigration auf neuen PC',
    'Drucker-Treiber aktualisiert',
]

zahlungsarten = ['Bar', 'Rechnung', 'Twint', 'Überweisung']

heute = datetime.now()
for i in range(25):
    kunde_id = random.choice(kunde_ids)
    datum = (heute - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
    dauer = random.choice([30, 45, 60, 90, 120, 180])
    thema = random.choice(themen)
    kosten = round(dauer * 1.5, 2)  # CHF 1.50 pro Minute als Beispiel
    bezahlt = random.choice([0, 1, 1])  # 2/3 bezahlt
    zahlungsart = random.choice(zahlungsarten) if bezahlt else ''
    
    cursor.execute(
        'INSERT INTO rapporte (kunde_id, datum, dauer_minuten, thema, kosten, bezahlt, zahlungsart) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (kunde_id, datum, dauer, thema, kosten, bezahlt, zahlungsart)
    )

print(f"  ✓ 25 Rapporte hinzugefügt")

# Änderungen speichern
conn.commit()
conn.close()

print("\n✅ Alle Testdaten erfolgreich eingefügt!")
print(f"\nÖffne http://localhost:8085 um die Daten zu sehen.")
