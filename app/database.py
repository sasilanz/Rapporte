import sqlite3
from flask import current_app, g

def get_db():
    """Hole oder erstelle Datenbankverbindung"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    """Initialisiere Datenbank mit Schema"""
    db = get_db()
    
    # Kunden Tabelle
    db.execute('''
        CREATE TABLE IF NOT EXISTS kunden (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            telefon TEXT,
            adresse TEXT,
            it_infrastruktur TEXT,
            stundensatz REAL DEFAULT 120.0,
            erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Login-Daten Tabelle
    db.execute('''
        CREATE TABLE IF NOT EXISTS login_daten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kunde_id INTEGER NOT NULL,
            geraet_typ TEXT NOT NULL,
            beschreibung TEXT,
            username TEXT,
            passwort TEXT,
            erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (kunde_id) REFERENCES kunden (id)
        )
    ''')
    
    # Rapporte Tabelle
    db.execute('''
        CREATE TABLE IF NOT EXISTS rapporte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kunde_id INTEGER NOT NULL,
            datum DATE NOT NULL,
            dauer_minuten INTEGER NOT NULL,
            thema TEXT NOT NULL,
            kosten REAL,
            bezahlt BOOLEAN DEFAULT 0,
            zahlungsart TEXT,
            erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (kunde_id) REFERENCES kunden (id)
        )
    ''')
    
    db.commit()
