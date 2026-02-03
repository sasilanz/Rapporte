from flask import Flask, render_template, request, redirect, url_for, Response, make_response
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash
from app.database import init_db, get_db
import os
import csv
from io import StringIO, BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from datetime import datetime
from qrbill import QRBill
from svglib.svglib import svg2rlg

app = Flask(__name__)
app.config['DATABASE'] = os.environ.get('DATABASE_PATH', '/app/data/rapporte.db')
app.config['TEMPLATES_AUTO_RELOAD'] = True

# HTTP Basic Auth Setup
auth = HTTPBasicAuth()

# Benutzer und Passwörter (Passwort-Hashes)
# Generiere Hash mit: from werkzeug.security import generate_password_hash; print(generate_password_hash('dein_passwort'))
users = {
    os.environ.get('AUTH_USERNAME', 'admin'): os.environ.get('AUTH_PASSWORD_HASH', 'scrypt:32768:8:1$4xQJ5Z8LGFqPHYmH$c8e0c3d8a5f5e9c8b0f1e3d7a9c6b4f2e1d8a7b5c3f0e2d9a8b6c4f1e3d7a9c5b2f0e1d8a7b6c3f2e0d9a8b5c4f1e3d7')
}

# Payment/Rechnungs-Konfiguration
PAYEE_CONFIG = {
    'legal_name': os.environ.get('PAYEE_LEGAL_NAME', ''),
    'iban': os.environ.get('PAYEE_IBAN', ''),
    'bank': os.environ.get('PAYEE_BANK', ''),
    'bic': os.environ.get('PAYEE_BIC', ''),
    'display_name': os.environ.get('PAYEE_DISPLAY_NAME', ''),
    'address_line1': os.environ.get('PAYEE_ADDRESS_LINE1', ''),
    'address_line2': os.environ.get('PAYEE_ADDRESS_LINE2', ''),
    'country': os.environ.get('PAYEE_COUNTRY', 'CH')
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

# Initialisiere Datenbank beim Start
with app.app_context():
    init_db()

def format_date_ch(date_str):
    """Konvertiert Datum zu CH-Format (DD.MM.YYYY)"""
    if not date_str:
        return ''
    # Konvertiere zu String falls nötig
    date_str = str(date_str)
    # Format: YYYY-MM-DD -> DD.MM.YYYY
    if '-' in date_str and len(date_str) >= 10:
        parts = date_str[:10].split('-')
        if len(parts) == 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
    return date_str

def generiere_rechnungsnummer():
    """Generiert eindeutige Rechnungsnummer im Format RE-YYYYMMDD-XXXXX"""
    db = get_db()
    today = datetime.now().strftime("%Y%m%d")

    # Zähle Rechnungen von heute
    count = db.execute(
        "SELECT COUNT(*) as cnt FROM rechnungen WHERE rechnungs_nummer LIKE ?",
        (f"RE-{today}-%",)
    ).fetchone()['cnt']

    return f"RE-{today}-{count+1:05d}"

def generiere_qr_rechnung(betrag, kunde, rechnungs_nummer):
    """Generiert Swiss QR Bill als ReportLab Drawing"""

    if not PAYEE_CONFIG['iban']:
        raise ValueError("PAYEE_IBAN nicht konfiguriert")

    # Nutze strukturierte Adressfelder (neue Struktur)
    kunde_strasse = kunde.get('strasse', '') or ''
    kunde_hausnummer = kunde.get('hausnummer', '') or ''
    kunde_plz = kunde.get('plz', '') or ''
    kunde_stadt = kunde.get('stadt', '') or ''

    # Vollständige Strasse für QR Bill
    kunde_strasse_komplett = f"{kunde_strasse} {kunde_hausnummer}".strip() if kunde_strasse else ''

    # Creditor (Rechnungssteller)
    creditor_plz_ort = PAYEE_CONFIG['address_line2'].split(maxsplit=1)
    creditor_data = {
        'name': PAYEE_CONFIG['legal_name'],
        'pcode': creditor_plz_ort[0] if len(creditor_plz_ort) > 0 else '8000',
        'city': creditor_plz_ort[1] if len(creditor_plz_ort) > 1 else 'Zürich',
        'country': PAYEE_CONFIG['country']
    }

    # Debtor (Kunde) - optional
    debtor_data = None
    if kunde.get('name') and kunde_plz and kunde_stadt:
        debtor_data = {
            'name': kunde['name'],
            'street': kunde_strasse_komplett or None,
            'pcode': kunde_plz,
            'city': kunde_stadt,
            'country': 'CH'
        }

    # QR Bill erstellen
    bill = QRBill(
        account=PAYEE_CONFIG['iban'],
        creditor=creditor_data,
        amount=f"{betrag:.2f}",
        debtor=debtor_data,
        additional_information=f"Rechnung Nr. {rechnungs_nummer}",
        language='de'  # Deutsch für Schweizer Senioren
    )

    # SVG generieren und zu Drawing konvertieren
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(suffix='.svg', delete=False) as tmp:
        bill.as_svg(tmp.name)
        drawing = svg2rlg(tmp.name)

    return drawing

def erstelle_rechnung_pdf(rapport, kunde, rechnungs_nummer):
    """Erstellt vollständige Rechnung mit QR Bill für einen Rapport"""

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    elements = []
    styles = getSampleStyleSheet()

    # === HEADER / ABSENDER ===
    elements.append(Paragraph(f'<b>{PAYEE_CONFIG["display_name"]}</b>', styles['Title']))
    elements.append(Paragraph(PAYEE_CONFIG['address_line1'], styles['Normal']))
    elements.append(Paragraph(PAYEE_CONFIG['address_line2'], styles['Normal']))
    elements.append(Spacer(1, 1*cm))

    # === KUNDE & RECHNUNG INFO ===
    heute = format_date_ch(datetime.now().strftime('%Y-%m-%d'))

    # Baue Kundenadresse aus strukturierten Feldern
    kunde_adresse_zeilen = []
    strasse_komplett = f"{kunde.get('strasse', '')} {kunde.get('hausnummer', '')}".strip()
    if strasse_komplett:
        kunde_adresse_zeilen.append(strasse_komplett)
    plz_stadt = f"{kunde.get('plz', '')} {kunde.get('stadt', '')}".strip()
    if plz_stadt:
        kunde_adresse_zeilen.append(plz_stadt)

    kunde_info = f"""
    <b>{kunde['name']}</b><br/>
    {'<br/>'.join(kunde_adresse_zeilen)}
    """
    rechnung_info = f"""
    <b>Datum:</b> {heute}<br/>
    <b>Rechnung Nr.:</b> {rechnungs_nummer}
    """

    info_table = Table([
        [Paragraph(kunde_info, styles['Normal']),
         Paragraph(rechnung_info, styles['Normal'])]
    ], colWidths=[10*cm, 7*cm])
    elements.append(info_table)
    elements.append(Spacer(1, 1.5*cm))

    # === TITEL ===
    elements.append(Paragraph('<b>RECHNUNG</b>', styles['Heading2']))
    elements.append(Spacer(1, 0.5*cm))

    # === POSITIONEN TABELLE ===
    data = [['Pos', 'Datum', 'Beschreibung', 'Dauer', 'Betrag (CHF)']]

    # Beschreibung als Paragraph mit erhaltenen Zeilenumbrüchen
    thema_mit_br = rapport['thema'].replace('\n', '<br/>')
    beschreibung_para = Paragraph(thema_mit_br, styles['Normal'])
    dauer_std = rapport['dauer_minuten'] / 60

    data.append([
        '1',
        format_date_ch(rapport['datum']),
        beschreibung_para,  # Paragraph statt Text für Wrapping
        f"{rapport['dauer_minuten']} min",
        f"{rapport['kosten']:.2f}"
    ])

    # Total Zeile (ohne HTML-Tags, Formatierung via TableStyle)
    data.append(['', '', '', 'Total CHF:', f"{rapport['kosten']:.2f}"])

    table = Table(data, colWidths=[1.5*cm, 2.5*cm, 8*cm, 2.5*cm, 2.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Text oben ausrichten (für mehrzeilige Beschreibung)
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('LINEABOVE', (3, -1), (-1, -1), 2, colors.black),
        ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),  # Total-Zeile fett
    ]))

    elements.append(table)
    elements.append(Spacer(1, 1*cm))

    # === ZAHLUNGSSTATUS ===
    if rapport['bezahlt']:
        # Rechnung bereits bezahlt - Zeige Bezahlt-Vermerk
        elements.append(Paragraph('<b style="color:green;">✓ BEZAHLT</b>', styles['Heading2']))
        if rapport['zahlungsart']:
            elements.append(Paragraph(f'Zahlungsart: {rapport["zahlungsart"]}', styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph('Vielen Dank für Ihr Vertrauen!', styles['Normal']))
    else:
        # Rechnung offen - Zeige Zahlungsbedingungen und QR-Code
        elements.append(Paragraph('Zahlbar innert 30 Tagen', styles['Normal']))
        elements.append(Spacer(1, 1*cm))

        # === QR BILL ===
        try:
            qr_drawing = generiere_qr_rechnung(rapport['kosten'], kunde, rechnungs_nummer)
            if qr_drawing:
                # Skaliere auf passende Grösse
                qr_drawing.width = 17*cm
                qr_drawing.height = 10.5*cm
                qr_drawing.scale(1, 1)
                elements.append(qr_drawing)
        except Exception as e:
            error_text = f'<b style="color:red">FEHLER:</b> QR-Rechnung konnte nicht generiert werden: {str(e)}'
            elements.append(Paragraph(error_text, styles['Normal']))

    # PDF erstellen
    doc.build(elements)
    buffer.seek(0)

    return buffer.getvalue()

app.jinja_env.filters['date_ch'] = format_date_ch

@app.route('/')
@auth.login_required
def index():
    """Hauptseite mit Übersicht der letzten Rapporte mit Filter"""
    db = get_db()
    
    # Filter-Parameter
    kunde_id = request.args.get('kunde_id', '')
    von_datum = request.args.get('von_datum', '')
    bis_datum = request.args.get('bis_datum', '')
    bezahlt_filter = request.args.get('bezahlt', '')
    
    # Base Query
    query = 'SELECT r.*, k.name as kunde_name FROM rapporte r LEFT JOIN kunden k ON r.kunde_id = k.id WHERE 1=1'
    params = []
    
    if kunde_id:
        query += ' AND r.kunde_id = ?'
        params.append(kunde_id)
    if von_datum:
        query += ' AND r.datum >= ?'
        params.append(von_datum)
    if bis_datum:
        query += ' AND r.datum <= ?'
        params.append(bis_datum)
    if bezahlt_filter == '1':
        query += ' AND r.bezahlt = 1'
    elif bezahlt_filter == '0':
        query += ' AND r.bezahlt = 0'
    
    query += ' ORDER BY r.datum DESC'
    
    rapporte = db.execute(query, params).fetchall()
    kunden = db.execute('SELECT id, name FROM kunden ORDER BY name').fetchall()
    
    # Formatiere Datum im Python-Code
    rapporte_formatted = []
    for r in rapporte:
        r_dict = {}
        for key in r.keys():
            if key == 'datum':
                r_dict[key] = format_date_ch(r[key])  # Überschreibe datum mit formatiertem Wert
            else:
                r_dict[key] = r[key]
        rapporte_formatted.append(r_dict)
    
    return render_template('index.html', rapporte=rapporte_formatted, kunden=kunden,
                         filters={'kunde_id': kunde_id, 'von_datum': von_datum, 
                                'bis_datum': bis_datum, 'bezahlt': bezahlt_filter})

@app.route('/kunden')
@auth.login_required
def kunden_liste():
    """Liste aller Kunden"""
    db = get_db()
    kunden = db.execute('SELECT * FROM kunden ORDER BY name').fetchall()
    return render_template('kunden.html', kunden=kunden)

@app.route('/kunden/neu', methods=['GET', 'POST'])
@auth.login_required
def kunde_neu():
    """Neuen Kunden erfassen"""
    if request.method == 'POST':
        db = get_db()
        db.execute(
            'INSERT INTO kunden (name, email, telefon, strasse, hausnummer, plz, stadt, it_infrastruktur, stundensatz) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (request.form['name'], request.form['email'], request.form['telefon'],
             request.form.get('strasse', ''), request.form.get('hausnummer', ''),
             request.form.get('plz', ''), request.form.get('stadt', ''),
             request.form['it_infrastruktur'], request.form.get('stundensatz', 120.0))
        )
        db.commit()
        return redirect(url_for('kunden_liste'))
    return render_template('kunde_form.html')


@app.route('/rapporte/neu', methods=['GET', 'POST'])
@auth.login_required
def rapport_neu():
    """Neuen Rapport erfassen"""
    if request.method == 'POST':
        db = get_db()
        
        # Berechne Kosten automatisch wenn nicht angegeben
        kosten = request.form.get('kosten')
        if not kosten or kosten == '':
            kunde_id = request.form['kunde_id']
            dauer_minuten = int(request.form['dauer'])
            kunde = db.execute('SELECT stundensatz FROM kunden WHERE id = ?', (kunde_id,)).fetchone()
            stundensatz = kunde['stundensatz'] if kunde else 120.0
            kosten = round((dauer_minuten / 60.0) * stundensatz, 2)
        
        db.execute(
            'INSERT INTO rapporte (kunde_id, datum, dauer_minuten, thema, kosten, bezahlt, zahlungsart) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (request.form['kunde_id'], request.form['datum'], request.form['dauer'],
             request.form['thema'], kosten, 
             'bezahlt' in request.form, request.form.get('zahlungsart', ''))
        )
        db.commit()
        return redirect(url_for('index'))
    
    db = get_db()
    kunden = db.execute('SELECT id, name, stundensatz FROM kunden ORDER BY name').fetchall()
    return render_template('rapport_form.html', kunden=kunden)

@app.route('/rapporte/<int:rapport_id>/bearbeiten', methods=['GET', 'POST'])
@auth.login_required
def rapport_bearbeiten(rapport_id):
    """Rapport bearbeiten"""
    db = get_db()
    
    if request.method == 'POST':
        # Berechne Kosten automatisch wenn nicht angegeben
        kosten = request.form.get('kosten')
        if not kosten or kosten == '':
            kunde_id = request.form['kunde_id']
            dauer_minuten = int(request.form['dauer'])
            kunde = db.execute('SELECT stundensatz FROM kunden WHERE id = ?', (kunde_id,)).fetchone()
            stundensatz = kunde['stundensatz'] if kunde else 120.0
            kosten = round((dauer_minuten / 60.0) * stundensatz, 2)
        
        db.execute(
            'UPDATE rapporte SET kunde_id=?, datum=?, dauer_minuten=?, thema=?, kosten=?, bezahlt=?, zahlungsart=? WHERE id=?',
            (request.form['kunde_id'], request.form['datum'], request.form['dauer'],
             request.form['thema'], kosten,
             'bezahlt' in request.form, request.form.get('zahlungsart', ''), rapport_id)
        )
        db.commit()
        return redirect(url_for('index'))
    
    rapport = db.execute('SELECT * FROM rapporte WHERE id = ?', (rapport_id,)).fetchone()
    kunden = db.execute('SELECT id, name, stundensatz FROM kunden ORDER BY name').fetchall()
    return render_template('rapport_form.html', rapport=rapport, kunden=kunden, edit_mode=True)

@app.route('/kunden/<int:kunde_id>')
@auth.login_required
def kunde_detail(kunde_id):
    """Kundendetails mit Login-Daten und Rapporten"""
    db = get_db()
    kunde = db.execute('SELECT * FROM kunden WHERE id = ?', (kunde_id,)).fetchone()
    logins = db.execute('SELECT * FROM login_daten WHERE kunde_id = ?', (kunde_id,)).fetchall()
    rapporte = db.execute('SELECT * FROM rapporte WHERE kunde_id = ? ORDER BY datum DESC', (kunde_id,)).fetchall()
    return render_template('kunde_detail.html', kunde=kunde, logins=logins, rapporte=rapporte)

@app.route('/kunden/<int:kunde_id>/bearbeiten', methods=['GET', 'POST'])
@auth.login_required
def kunde_bearbeiten(kunde_id):
    """Kunde bearbeiten"""
    db = get_db()

    if request.method == 'POST':
        db.execute(
            'UPDATE kunden SET name=?, email=?, telefon=?, strasse=?, hausnummer=?, plz=?, stadt=?, it_infrastruktur=?, stundensatz=? WHERE id=?',
            (request.form['name'], request.form['email'], request.form['telefon'],
             request.form.get('strasse', ''), request.form.get('hausnummer', ''),
             request.form.get('plz', ''), request.form.get('stadt', ''),
             request.form['it_infrastruktur'], request.form.get('stundensatz', 120.0), kunde_id)
        )
        db.commit()
        return redirect(url_for('kunde_detail', kunde_id=kunde_id))

    kunde = db.execute('SELECT * FROM kunden WHERE id = ?', (kunde_id,)).fetchone()
    return render_template('kunde_form.html', kunde=kunde, edit_mode=True)

@app.route('/login-daten/<int:kunde_id>/neu', methods=['GET', 'POST'])
@auth.login_required
def login_neu(kunde_id):
    """Neue Login-Daten für Kunde erfassen"""
    if request.method == 'POST':
        db = get_db()
        db.execute(
            'INSERT INTO login_daten (kunde_id, geraet_typ, beschreibung, username, passwort) '
            'VALUES (?, ?, ?, ?, ?)',
            (kunde_id, request.form['geraet_typ'], request.form['beschreibung'],
             request.form['username'], request.form['passwort'])
        )
        db.commit()
        return redirect(url_for('kunde_detail', kunde_id=kunde_id))

    db = get_db()
    kunde = db.execute('SELECT * FROM kunden WHERE id = ?', (kunde_id,)).fetchone()
    return render_template('login_form.html', kunde=kunde)

@app.route('/login-daten/<int:login_id>/bearbeiten', methods=['GET', 'POST'])
@auth.login_required
def login_bearbeiten(login_id):
    """Login-Daten bearbeiten"""
    db = get_db()

    if request.method == 'POST':
        db.execute(
            'UPDATE login_daten SET geraet_typ=?, beschreibung=?, username=?, passwort=? WHERE id=?',
            (request.form['geraet_typ'], request.form['beschreibung'],
             request.form['username'], request.form['passwort'], login_id)
        )
        db.commit()
        login = db.execute('SELECT kunde_id FROM login_daten WHERE id = ?', (login_id,)).fetchone()
        return redirect(url_for('kunde_detail', kunde_id=login['kunde_id']))

    login = db.execute('SELECT * FROM login_daten WHERE id = ?', (login_id,)).fetchone()
    kunde = db.execute('SELECT * FROM kunden WHERE id = ?', (login['kunde_id'],)).fetchone()
    return render_template('login_form.html', kunde=kunde, login=login, edit_mode=True)

@app.route('/login-daten/<int:login_id>/loeschen', methods=['POST'])
@auth.login_required
def login_loeschen(login_id):
    """Login-Daten löschen"""
    db = get_db()
    login = db.execute('SELECT kunde_id FROM login_daten WHERE id = ?', (login_id,)).fetchone()
    kunde_id = login['kunde_id']
    db.execute('DELETE FROM login_daten WHERE id = ?', (login_id,))
    db.commit()
    return redirect(url_for('kunde_detail', kunde_id=kunde_id))

@app.route('/kunden/<int:kunde_id>/loeschen', methods=['POST'])
@auth.login_required
def kunde_loeschen(kunde_id):
    """Kunde und alle zugehörigen Daten löschen"""
    db = get_db()
    # Lösche zuerst abhängige Daten
    db.execute('DELETE FROM login_daten WHERE kunde_id = ?', (kunde_id,))
    db.execute('DELETE FROM rapporte WHERE kunde_id = ?', (kunde_id,))
    db.execute('DELETE FROM kunden WHERE id = ?', (kunde_id,))
    db.commit()
    return redirect(url_for('kunden_liste'))

@app.route('/export/csv')
@auth.login_required
def export_csv():
    """Exportiere gefilterte Rapporte als CSV"""
    db = get_db()
    
    # Gleiche Filter wie auf Hauptseite
    kunde_id = request.args.get('kunde_id', '')
    von_datum = request.args.get('von_datum', '')
    bis_datum = request.args.get('bis_datum', '')
    bezahlt_filter = request.args.get('bezahlt', '')
    
    query = 'SELECT r.datum, k.name as kunde, r.thema, r.dauer_minuten, r.kosten, r.bezahlt, r.zahlungsart FROM rapporte r LEFT JOIN kunden k ON r.kunde_id = k.id WHERE 1=1'
    params = []
    
    if kunde_id:
        query += ' AND r.kunde_id = ?'
        params.append(kunde_id)
    if von_datum:
        query += ' AND r.datum >= ?'
        params.append(von_datum)
    if bis_datum:
        query += ' AND r.datum <= ?'
        params.append(bis_datum)
    if bezahlt_filter == '1':
        query += ' AND r.bezahlt = 1'
    elif bezahlt_filter == '0':
        query += ' AND r.bezahlt = 0'
    
    query += ' ORDER BY r.datum DESC'
    rapporte = db.execute(query, params).fetchall()
    
    # CSV erstellen
    si = StringIO()
    writer = csv.writer(si, delimiter=';')
    writer.writerow(['Datum', 'Kunde', 'Thema', 'Dauer (Min)', 'Kosten (CHF)', 'Bezahlt', 'Zahlungsart'])
    
    for r in rapporte:
        writer.writerow([
            format_date_ch(r['datum']),
            r['kunde'],
            r['thema'],
            r['dauer_minuten'],
            f"{r['kosten']:.2f}" if r['kosten'] else '0.00',
            'Ja' if r['bezahlt'] else 'Nein',
            r['zahlungsart'] or ''
        ])
    
    output = si.getvalue()
    si.close()
    
    response = Response(output, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=rapporte_{datetime.now().strftime("%Y%m%d")}.csv'
    return response

@app.route('/export/pdf')
@auth.login_required
def export_pdf():
    """Exportiere gefilterte Rapporte als PDF"""
    db = get_db()
    
    # Gleiche Filter wie auf Hauptseite
    kunde_id = request.args.get('kunde_id', '')
    von_datum = request.args.get('von_datum', '')
    bis_datum = request.args.get('bis_datum', '')
    bezahlt_filter = request.args.get('bezahlt', '')
    
    query = 'SELECT r.datum, k.name as kunde, r.thema, r.dauer_minuten, r.kosten, r.bezahlt, r.zahlungsart FROM rapporte r LEFT JOIN kunden k ON r.kunde_id = k.id WHERE 1=1'
    params = []
    
    if kunde_id:
        query += ' AND r.kunde_id = ?'
        params.append(kunde_id)
    if von_datum:
        query += ' AND r.datum >= ?'
        params.append(von_datum)
    if bis_datum:
        query += ' AND r.datum <= ?'
        params.append(bis_datum)
    if bezahlt_filter == '1':
        query += ' AND r.bezahlt = 1'
    elif bezahlt_filter == '0':
        query += ' AND r.bezahlt = 0'
    
    query += ' ORDER BY r.datum DESC'
    rapporte = db.execute(query, params).fetchall()
    
    # PDF erstellen
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph('<b>Rapporte Übersicht</b>', styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))
    
    # Filter-Info
    filter_info = []
    if von_datum:
        filter_info.append(f"Von: {format_date_ch(von_datum)}")
    if bis_datum:
        filter_info.append(f"Bis: {format_date_ch(bis_datum)}")
    if filter_info:
        elements.append(Paragraph(' | '.join(filter_info), styles['Normal']))
        elements.append(Spacer(1, 0.3*cm))
    
    # Tabelle
    data = [['Datum', 'Kunde', 'Thema', 'Dauer\n(Min)', 'Kosten\n(CHF)', 'Status']]
    
    total_kosten = 0
    for r in rapporte:
        kosten = r['kosten'] or 0
        total_kosten += kosten
        status = f"✓ {r['zahlungsart']}" if r['bezahlt'] else '⏳ Offen'
        data.append([
            format_date_ch(r['datum']),
            r['kunde'],
            r['thema'][:30] + '...' if len(r['thema']) > 30 else r['thema'],
            str(r['dauer_minuten']),
            f"{kosten:.2f}",
            status
        ])
    
    # Summe
    data.append(['', '', '', '', f"Total: {total_kosten:.2f}", ''])
    
    table = Table(data, colWidths=[2.5*cm, 3.5*cm, 6*cm, 2*cm, 2*cm, 2.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=rapporte_{datetime.now().strftime("%Y%m%d")}.pdf'
    return response

@app.route('/rechnung/rapport/<int:rapport_id>')
@auth.login_required
def rechnung_einzeln(rapport_id):
    """Erstellt Rechnung für einzelnen Rapport"""
    db = get_db()

    # Lade Rapport mit Kundendaten
    row = db.execute('''
        SELECT r.*, k.name as kunde_name, k.email, k.telefon, k.adresse,
               k.strasse, k.hausnummer, k.plz, k.stadt,
               k.it_infrastruktur, k.stundensatz
        FROM rapporte r
        JOIN kunden k ON r.kunde_id = k.id
        WHERE r.id = ?
    ''', (rapport_id,)).fetchone()

    if not row:
        return "Rapport nicht gefunden", 404

    # Konvertiere zu Dicts für einfacheren Zugriff
    rapport = {
        'id': row['id'],
        'kunde_id': row['kunde_id'],
        'datum': row['datum'],
        'dauer_minuten': row['dauer_minuten'],
        'thema': row['thema'],
        'kosten': row['kosten'],
        'bezahlt': row['bezahlt'],
        'zahlungsart': row['zahlungsart']
    }
    kunde = {
        'name': row['kunde_name'],
        'email': row['email'],
        'adresse': row['adresse'],  # Fallback für alte Daten
        'strasse': row['strasse'],
        'hausnummer': row['hausnummer'],
        'plz': row['plz'],
        'stadt': row['stadt']
    }

    # Validierung
    if not PAYEE_CONFIG['iban']:
        return "Fehler: IBAN nicht konfiguriert. Bitte PAYEE_IBAN in docker-compose.yml setzen.", 500

    if not rapport['kosten'] or rapport['kosten'] <= 0:
        return "Fehler: Rapport hat keinen gültigen Betrag.", 400

    # Generiere Rechnungsnummer
    rechnungs_nummer = generiere_rechnungsnummer()

    # Speichere Rechnung in DB
    db.execute(
        'INSERT INTO rechnungen (rechnungs_nummer, kunde_id, betrag, rapport_ids) VALUES (?, ?, ?, ?)',
        (rechnungs_nummer, rapport['kunde_id'], rapport['kosten'], str(rapport_id))
    )
    db.commit()

    # Generiere PDF
    try:
        pdf_bytes = erstelle_rechnung_pdf(rapport, kunde, rechnungs_nummer)
    except Exception as e:
        return f"Fehler beim Erstellen der Rechnung: {str(e)}", 500

    # Rückgabe als Download
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Rechnung_{rechnungs_nummer}.pdf'

    return response

@app.teardown_appcontext
def close_connection(exception):
    """Schließe Datenbankverbindung"""
    db = getattr(Flask, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, debug=True)
