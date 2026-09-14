import os
import json
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template_string, redirect, url_for, flash, current_app

export_bp = Blueprint('export_manager', __name__)

DOC_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "docx", "xlsx"}

def allowed_doc_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in DOC_EXTENSIONS

def get_db():
    from server import get_db as server_get_db
    return server_get_db()

def make_doc_url(filename):
    if not filename:
        return None
    return f"/uploads/{filename}"

# ==================== VERİTABANI OLUŞTURMA & SEED ====================

def init_export_db(conn):
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS export_shipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_no TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        country TEXT NOT NULL,
        destination_port TEXT,
        incoterm TEXT DEFAULT 'FOB',
        transport_mode TEXT DEFAULT 'sea',
        carrier_forwarder TEXT,
        loading_date TEXT,
        cutoff_datetime TEXT,
        etd TEXT,
        eta TEXT,
        status TEXT DEFAULT 'preparing',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS export_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT DEFAULT 'document',
        is_completed INTEGER DEFAULT 0,
        completed_at TEXT,
        due_datetime TEXT,
        document_file_url TEXT,
        tracking_code TEXT,
        notes TEXT,
        priority TEXT DEFAULT 'normal',
        FOREIGN KEY(shipment_id) REFERENCES export_shipments(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS export_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id INTEGER NOT NULL,
        task_id INTEGER,
        alert_type TEXT NOT NULL,
        severity TEXT DEFAULT 'warning',
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_resolved INTEGER DEFAULT 0,
        snooze_until TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(shipment_id) REFERENCES export_shipments(id) ON DELETE CASCADE,
        FOREIGN KEY(task_id) REFERENCES export_tasks(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS export_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        value TEXT
    );
    """)

    try:
        cursor.execute("SELECT notif_type FROM notifications LIMIT 1")
    except Exception:
        try:
            cursor.execute("ALTER TABLE notifications ADD COLUMN notif_type TEXT DEFAULT 'ihracat'")
        except Exception:
            pass

    # Seed Default Settings
    default_settings = [
        ("telegram_bot_token", ""),
        ("telegram_chat_id", ""),
        ("auto_push_fcm", "1"),
        ("daily_morning_summary", "1")
    ]
    for k, v in default_settings:
        cursor.execute("INSERT OR IGNORE INTO export_settings (key, value) VALUES (?, ?)", (k, v))

    # Seed Demo Shipments & Tasks if table is empty
    cursor.execute("SELECT COUNT(*) FROM export_shipments")
    if cursor.fetchone()[0] == 0:
        now = datetime.now()
        
        # 1. Almanya Denizyolu (Cut-off Yaklaşıyor & Eksik Evrak Uyarılı)
        s1_cutoff = (now + timedelta(hours=28)).strftime('%Y-%m-%d %H:%M')
        s1_etd = (now + timedelta(days=2)).strftime('%Y-%m-%d')
        s1_eta = (now + timedelta(days=14)).strftime('%Y-%m-%d')
        s1_load = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        cursor.execute("""
        INSERT INTO export_shipments (file_no, customer_name, country, destination_port, incoterm, transport_mode, carrier_forwarder, loading_date, cutoff_datetime, etd, eta, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "EXP-2026-DE-001", "MedTech Healthcare GmbH", "Almanya", "Hamburg Limanı", "FOB", "sea",
            "Maersk Line / Kuehne+Nagel", s1_load, s1_cutoff, s1_etd, s1_eta, "preparing",
            "2x40HC Tıbbi Flaster ve Elastik Bandaj sevkiyatı. Gemiye yükleme acil."
        ))
        s1_id = cursor.lastrowid
        
        # 2. İtalya Karayolu (Geciken Evrak Uyarılı)
        s2_etd = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        s2_eta = (now + timedelta(days=4)).strftime('%Y-%m-%d')
        s2_load = (now - timedelta(days=2)).strftime('%Y-%m-%d')
        cursor.execute("""
        INSERT INTO export_shipments (file_no, customer_name, country, destination_port, incoterm, transport_mode, carrier_forwarder, loading_date, cutoff_datetime, etd, eta, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "EXP-2026-IT-002", "Sanitaria Pharma Nord S.r.l.", "İtalya", "Milano Terminali", "DAP", "road",
            "Ekol Lojistik (Tır)", s2_load, None, s2_etd, s2_eta, "customs",
            "Kapı teslimi medikal sarf malzemesi ihracatı."
        ))
        s2_id = cursor.lastrowid

        # 3. Mısır Denizyolu (Yolda - Orijinal Kargo Evrakı Bekleyen)
        s3_etd = (now - timedelta(days=4)).strftime('%Y-%m-%d')
        s3_eta = (now + timedelta(days=9)).strftime('%Y-%m-%d')
        cursor.execute("""
        INSERT INTO export_shipments (file_no, customer_name, country, destination_port, incoterm, transport_mode, carrier_forwarder, loading_date, cutoff_datetime, etd, eta, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "EXP-2026-EG-003", "Cairo Medical Supply Co.", "Mısır", "İskenderiye Limanı", "CIF", "sea",
            "MSC Mediterranean Shipping", (now - timedelta(days=5)).strftime('%Y-%m-%d'), None, s3_etd, s3_eta, "in_transit",
            "Akreditifli satış (L/C). Orijinal konşimento ve faturalar müşteriye kargolanmalı."
        ))
        s3_id = cursor.lastrowid

        # Seed Tasks for S1 (Almanya)
        tasks_s1 = [
            (s1_id, "Ticari Fatura (Commercial Invoice)", "document", 1, now.strftime('%Y-%m-%d %H:%M'), None, None, None, "Fatura kesildi ve onaylandı.", "urgent"),
            (s1_id, "Çeki Listesi (Packing List)", "document", 1, now.strftime('%Y-%m-%d %H:%M'), None, None, None, "Depo koli adetleri doğrulandı.", "urgent"),
            (s1_id, "ATR Dolaşım Belgesi Düzenlenmesi", "document", 0, None, (now + timedelta(hours=20)).strftime('%Y-%m-%d %H:%M'), None, None, "Gümrükçüye tescil için iletilecek.", "normal"),
            (s1_id, "Konşimento Talimatı (BL Draft Instruction)", "transport", 0, None, (now + timedelta(hours=12)).strftime('%Y-%m-%d %H:%M'), None, None, "Acenteye acil iletilmeli! Cutoff'a az kaldı.", "urgent"),
            (s1_id, "İhracat Gümrük Beyannamesi Tescili", "customs", 0, None, s1_cutoff, None, None, "Gümrük müşavirinden teyit bekleniyor.", "urgent"),
            (s1_id, "Analiz & Kalite Sertifikası (COA / CE)", "document", 1, now.strftime('%Y-%m-%d %H:%M'), None, None, None, "Kalite kontrol raporu hazır.", "normal"),
            (s1_id, "Orijinal Evrak Kargosu (DHL/FedEx)", "courier", 0, None, (now + timedelta(days=3)).strftime('%Y-%m-%d %H:%M'), None, None, "Gemi kalktıktan sonra kargolanacak.", "urgent")
        ]
        cursor.executemany("""
        INSERT INTO export_tasks (shipment_id, title, category, is_completed, completed_at, due_datetime, document_file_url, tracking_code, notes, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tasks_s1)

        # Seed Tasks for S2 (İtalya - Overdue task)
        tasks_s2 = [
            (s2_id, "Ticari Fatura (Commercial Invoice)", "document", 1, now.strftime('%Y-%m-%d %H:%M'), None, None, None, "Tamamlandı", "urgent"),
            (s2_id, "Çeki Listesi (Packing List)", "document", 1, now.strftime('%Y-%m-%d %H:%M'), None, None, None, "Tamamlandı", "urgent"),
            (s2_id, "CMR Karayolu Taşıma Belgesi", "transport", 1, now.strftime('%Y-%m-%d %H:%M'), None, None, None, "Şoföre teslim edildi.", "urgent"),
            (s2_id, "EUR.1 Dolaşım Belgesi", "document", 0, None, (now - timedelta(hours=14)).strftime('%Y-%m-%d %H:%M'), None, None, "Dün onaylanması gerekiyordu, gecikmede!", "urgent"),
            (s2_id, "İhracat Gümrük Beyannamesi", "customs", 0, None, now.strftime('%Y-%m-%d 16:00'), None, None, "Kapıkule çıkışı bekleniyor.", "urgent")
        ]
        cursor.executemany("""
        INSERT INTO export_tasks (shipment_id, title, category, is_completed, completed_at, due_datetime, document_file_url, tracking_code, notes, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tasks_s2)

        # Seed Tasks for S3 (Mısır - In Transit, Kargo eksik)
        tasks_s3 = [
            (s3_id, "Ticari Fatura (Commercial Invoice)", "document", 1, now.strftime('%Y-%m-%d %H:%M'), None, None, None, "Onaylı", "urgent"),
            (s3_id, "Çeki Listesi (Packing List)", "document", 1, now.strftime('%Y-%m-%d %H:%M'), None, None, None, "Onaylı", "urgent"),
            (s3_id, "Menşe Şahadetnamesi (Mısır Konsolosluk Onaylı)", "document", 1, now.strftime('%Y-%m-%d %H:%M'), None, None, None, "Konsolosluk tasdiki yapıldı.", "normal"),
            (s3_id, "Orijinal Konşimento (Original B/L 3/3)", "transport", 1, now.strftime('%Y-%m-%d %H:%M'), None, None, None, "Acenteden asıllar teslim alındı.", "urgent"),
            (s3_id, "Orijinal Evrakların Alıcıya Kargolanması", "courier", 0, None, (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M'), None, None, "Gemi yola çıktı fakat kargo takip kodu girilmedi!", "urgent"),
            (s3_id, "Akreditif Bakiye Tahsilatı Teyidi", "payment", 0, None, (now + timedelta(days=10)).strftime('%Y-%m-%d %H:%M'), None, None, "Bankaya evrak ibrazı bekleniyor.", "normal")
        ]
        cursor.executemany("""
        INSERT INTO export_tasks (shipment_id, title, category, is_completed, completed_at, due_datetime, document_file_url, tracking_code, notes, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tasks_s3)

    conn.commit()


# ==================== STANDART GÖREV ŞABLONU OLUŞTURMA ====================

def create_default_tasks_for_shipment(conn, shipment_id, transport_mode="sea", incoterm="FOB", cutoff_str=None, etd_str=None):
    cursor = conn.cursor()
    now = datetime.now()
    
    # Referans tarih hesaplamaları
    due_invoice = (now + timedelta(days=1)).strftime('%Y-%m-%d 17:00')
    due_packing = (now + timedelta(days=1)).strftime('%Y-%m-%d 18:00')
    due_customs = cutoff_str if cutoff_str else (now + timedelta(days=2)).strftime('%Y-%m-%d 16:00')
    
    tasks = [
        ("Ticari Fatura (Commercial Invoice)", "document", "urgent", due_invoice, "Müşteri onaylı proforma doğrultusunda resmi faturanın hazırlanması."),
        ("Çeki Listesi (Packing List)", "document", "urgent", due_packing, "Brüt/Net ağırlıklar, hacim (cbm) ve koli detaylarının netleştirilmesi."),
        ("Dolaşım Belgesi (Menşe / ATR / EUR.1)", "document", "normal", due_customs, "Hedef ülkenin gümrük muafiyet belgesinin temini."),
        ("İhracat Gümrük Beyannamesi Tescili", "customs", "urgent", due_customs, "Gümrük müşavirine evrak aktarımı ve beyanname açılışı."),
        ("Müşteri Ödeme / Bakiye Kontrolü", "payment", "normal", None, "Sevkiyat öncesi anlaşmaya göre bakiye dekontunun teyidi."),
        ("Analiz / CE / Kalite Sertifikaları", "document", "normal", None, "Betasan ürün kalite ve lot kontrol raporları.")
    ]
    
    if transport_mode == "sea":
        tasks.extend([
            ("Gemi Konşimento Talimatı (BL Draft)", "transport", "urgent", due_customs, "Armatör veya acenteye B/L talimatının gönderilmesi."),
            ("Liman / Konteyner Cut-off Kapanış Takibi", "transport", "urgent", cutoff_str, "Konteynerin limana girişinin ve intaç onayının takibi."),
            ("Orijinal Konşimento (Original B/L) Alımı", "transport", "normal", None, "Geminin kalkışından sonra armatörden asıl konşimentoların alınması.")
        ])
    elif transport_mode == "road":
        tasks.extend([
            ("CMR Karayolu Taşıma Belgesi Düzenlenmesi", "transport", "urgent", due_customs, "Tır sürücüsü ve nakliyeci kaşeli CMR belgesi."),
            ("Araç Plaka & Şoför Bilgilerinin Alınması", "transport", "normal", None, "Gümrük kapı çıkışı için plaka teyidi.")
        ])
    elif transport_mode == "air":
        tasks.extend([
            ("AWB (Air Waybill) Hava Konşimentosu Kontrolü", "transport", "urgent", due_customs, "Hava kargo acentesinden AWB taslağının onaylanması.")
        ])
        
    tasks.append(("Orijinal Evrakların Müşteriye Kargolanması", "courier", "urgent", None, "DHL/FedEx/UPS ile asıl evrakların alıcıya gönderilmesi ve takip no kaydı."))

    for title, cat, prio, due, notes in tasks:
        cursor.execute("""
        INSERT INTO export_tasks (shipment_id, title, category, priority, due_datetime, notes, is_completed)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (shipment_id, title, cat, prio, due, notes))
        
    conn.commit()


# ==================== AKILLI BİLDİRİM & KURAL MOTORU ====================

def run_export_rule_engine(conn, force=False):
    """
    Tüm aktif ihracatları ve görevleri tarayarak:
    1. Cut-off yaklaşma uyarısı
    2. Kalkış (ETD) öncesi eksik evrak uyarısı
    3. Süresi geçmiş görev (Overdue) uyarısı
    4. Yola çıkmış sevkiyat için kargo takip kodu eksikliği uyarısı üretir.
    Üretilen alarmlar hem export_alerts tablosuna hem de mobil bildirim geçmişine işlenir.
    """
    cursor = conn.cursor()
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M')
    
    # Aktif sevkiyatları al
    cursor.execute("""
        SELECT * FROM export_shipments 
        WHERE status NOT IN ('completed', 'delivered')
    """)
    shipments = cursor.fetchall()
    
    generated_alerts = []

    for s in shipments:
        s_id = s["id"]
        file_no = s["file_no"]
        cust_name = s["customer_name"]
        country = s["country"]
        
        # Görevleri al
        cursor.execute("SELECT * FROM export_tasks WHERE shipment_id = ?", (s_id,))
        tasks = cursor.fetchall()
        
        # 1. KURAL: CUT-OFF YAKLAŞIYOR VEYA GEÇTİ Mİ?
        if s["cutoff_datetime"]:
            try:
                cutoff_dt = datetime.strptime(s["cutoff_datetime"][:16], '%Y-%m-%d %H:%M') if len(s["cutoff_datetime"]) > 10 else datetime.strptime(s["cutoff_datetime"][:10], '%Y-%m-%d')
                hours_left = (cutoff_dt - now).total_seconds() / 3600.0
                
                # Tamamlanmamış kritik görev var mı?
                uncompleted_critical = [t for t in tasks if t["is_completed"] == 0 and t["category"] in ('customs', 'transport', 'document')]
                
                if uncompleted_critical:
                    if 0 < hours_left <= 48:
                        sev = "danger" if hours_left <= 24 else "warning"
                        title = f"🚨 Cut-Off Yaklaşıyor: {file_no}"
                        msg = f"{cust_name} ({country}) ihracatının liman kapanışına (Cut-off) sadece {int(hours_left)} saat kaldı! {len(uncompleted_critical)} bekleyen evrak/işlem var."
                        _record_alert(cursor, s_id, None, "cutoff_approaching", sev, title, msg, generated_alerts)
                    elif hours_left < 0 and s["status"] in ('preparing', 'customs'):
                        title = f"⚠️ Cut-Off Süresi Doldu: {file_no}"
                        msg = f"{cust_name} ihracatının liman kapanış tarihi aşıldı fakat sevkiyat henüz yola çıkmadı!"
                        _record_alert(cursor, s_id, None, "cutoff_overdue", "danger", title, msg, generated_alerts)
            except Exception:
                pass

        # 2. KURAL: KALKIŞ (ETD) ÖNCESİ EKSİK EVRAK
        if s["etd"]:
            try:
                etd_dt = datetime.strptime(s["etd"][:10], '%Y-%m-%d')
                days_left = (etd_dt.date() - now.date()).days
                
                if 0 <= days_left <= 2:
                    for t in tasks:
                        if t["is_completed"] == 0 and t["priority"] == "urgent":
                            title = f"⏳ Kalkışa {days_left} Gün Kaldı - Eksik Evrak: {t['title']}"
                            msg = f"{file_no} ({cust_name}) sevkiyatının kalkışına çok az kaldı fakat '{t['title']}' henüz tamamlanmadı!"
                            _record_alert(cursor, s_id, t["id"], "missing_doc", "danger", title, msg, generated_alerts)
            except Exception:
                pass

        # 3. KURAL: SÜRESİ GEÇMİŞ GÖREV (OVERDUE TASK)
        for t in tasks:
            if t["is_completed"] == 0 and t["due_datetime"]:
                try:
                    due_dt = datetime.strptime(t["due_datetime"][:16], '%Y-%m-%d %H:%M') if len(t["due_datetime"]) > 10 else datetime.strptime(t["due_datetime"][:10], '%Y-%m-%d')
                    if now > due_dt:
                        title = f"🔴 Geciken Görev: {t['title']}"
                        msg = f"{file_no} ({cust_name}) dosyasındaki '{t['title']}' için belirlenen son tarih aşıldı! Lütfen aksiyon alın."
                        _record_alert(cursor, s_id, t["id"], "overdue_task", "danger", title, msg, generated_alerts)
                except Exception:
                    pass

        # 4. KURAL: YOLDA / KALKMIŞ VE ORİJİNAL EVRAK KARGOSU GİRİLMEMİŞ
        if s["status"] == "in_transit":
            courier_tasks = [t for t in tasks if t["category"] == "courier" or "Kargo" in t["title"]]
            for ct in courier_tasks:
                if ct["is_completed"] == 0 and not ct["tracking_code"]:
                    title = f"📦 Orijinal Evraklar Kargolandı mı? ({file_no})"
                    msg = f"{cust_name} yüklemesi yola çıktı. Müşterinin gümrük çekimi yapabilmesi için orijinal evrakların (B/L, Fatura) kargolanıp takip numarasının sisteme girilmesi gerekmektedir."
                    _record_alert(cursor, s_id, ct["id"], "courier_missing", "warning", title, msg, generated_alerts)

    conn.commit()
    
    # Telegram Bildirimi Tetikle (Yapılandırılmışsa)
    if generated_alerts:
        _trigger_external_notifications(conn, generated_alerts)
        
    return generated_alerts

def _record_alert(cursor, shipment_id, task_id, alert_type, severity, title, message, generated_list):
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M')
    
    # Bu alert türünde daha önce çözülmemiş veya ertelenmiş kayıt var mı kontrol et
    cursor.execute("""
        SELECT id, snooze_until, is_resolved FROM export_alerts
        WHERE shipment_id = ? AND alert_type = ? AND (task_id = ? OR (task_id IS NULL AND ? IS NULL))
        ORDER BY id DESC LIMIT 1
    """, (shipment_id, alert_type, task_id, task_id))
    existing = cursor.fetchone()
    
    if existing:
        # Eğer ertelenmişse ve süre dolmadıysa es geç
        if existing["snooze_until"] and existing["snooze_until"] > now_str:
            return
        # Eğer çözülmemişse tekrar mükerrer ekleme
        if existing["is_resolved"] == 0:
            return

    # Yeni alarm ekle
    cursor.execute("""
        INSERT INTO export_alerts (shipment_id, task_id, alert_type, severity, title, message, is_resolved)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (shipment_id, task_id, alert_type, severity, title, message))
    
    # Ayrıca mobil uygulama bildirimler tablosuna da ekle ki telefonda görünsün
    try:
        cursor.execute("""
            INSERT INTO notifications (title, message, target_product_id, notif_type)
            VALUES (?, ?, NULL, 'ihracat')
        """, (title, message))
    except Exception:
        cursor.execute("""
            INSERT INTO notifications (title, message, target_product_id)
            VALUES (?, ?, NULL)
        """, (title, message))
    
    generated_list.append({
        "shipment_id": shipment_id,
        "task_id": task_id,
        "alert_type": alert_type,
        "severity": severity,
        "title": title,
        "message": message
    })

def _trigger_external_notifications(conn, alerts):
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM export_settings")
    settings = dict(cursor.fetchall())
    
    bot_token = settings.get("telegram_bot_token", "").strip()
    chat_id = settings.get("telegram_chat_id", "").strip()
    
    if bot_token and chat_id:
        for a in alerts[:3]:
            send_telegram_msg(bot_token, chat_id, f"⚠️ *{a['title']}*\n\n{a['message']}")

def send_telegram_msg(token, chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ==================== WEB PANELİ GÖRÜNÜMLERİ ====================

@export_bp.route("/admin/exports")
def admin_exports():
    conn = get_db()
    
    # Kuralları arka planda çalıştırıp güncel alarmları tazele
    run_export_rule_engine(conn)
    
    cursor = conn.cursor()
    filter_mode = request.args.get("filter", "all")
    search = request.args.get("search", "").strip()

    # İstatistikler
    active_shipments_count = cursor.execute("SELECT COUNT(*) FROM export_shipments WHERE status NOT IN ('completed', 'delivered')").fetchone()[0]
    total_alerts_count = cursor.execute("SELECT COUNT(*) FROM export_alerts WHERE is_resolved = 0").fetchone()[0]
    urgent_tasks_count = cursor.execute("SELECT COUNT(*) FROM export_tasks WHERE is_completed = 0 AND priority = 'urgent'").fetchone()[0]
    completed_shipments_count = cursor.execute("SELECT COUNT(*) FROM export_shipments WHERE status = 'completed'").fetchone()[0]

    # Sevkiyat Sorgusu
    query = "SELECT * FROM export_shipments WHERE 1=1"
    params = []

    if filter_mode == "sea":
        query += " AND transport_mode = 'sea' AND status != 'completed'"
    elif filter_mode == "road":
        query += " AND transport_mode = 'road' AND status != 'completed'"
    elif filter_mode == "air":
        query += " AND transport_mode = 'air' AND status != 'completed'"
    elif filter_mode == "completed":
        query += " AND status = 'completed'"
    elif filter_mode == "active":
        query += " AND status NOT IN ('completed', 'delivered')"

    if search:
        query += " AND (file_no LIKE ? OR customer_name LIKE ? OR country LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    raw_shipments = cursor.fetchall()

    shipment_list = []
    for s in raw_shipments:
        cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as done FROM export_tasks WHERE shipment_id = ?", (s["id"],))
        stat = cursor.fetchone()
        total_t = stat["total"] or 0
        done_t = stat["done"] or 0
        pct = int((done_t / total_t * 100)) if total_t > 0 else 0

        alert_row = cursor.execute("SELECT COUNT(*) FROM export_alerts WHERE shipment_id = ? AND is_resolved = 0", (s["id"],)).fetchone()
        has_alert = alert_row[0] > 0

        shipment_list.append({
            "id": s["id"],
            "file_no": s["file_no"],
            "customer_name": s["customer_name"],
            "country": s["country"],
            "destination_port": s["destination_port"],
            "incoterm": s["incoterm"],
            "transport_mode": s["transport_mode"],
            "carrier_forwarder": s["carrier_forwarder"],
            "loading_date": s["loading_date"],
            "cutoff_datetime": s["cutoff_datetime"],
            "etd": s["etd"],
            "eta": s["eta"],
            "status": s["status"],
            "total_tasks": total_t,
            "done_tasks": done_t,
            "pct": pct,
            "has_alert": has_alert,
            "notes": s["notes"]
        })

    conn.close()

    content = """
    <div class="space-y-6">
        <!-- Başlık ve Hızlı Aksiyonlar -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <div class="flex items-center space-x-3">
                    <h1 class="text-2xl font-black text-slate-800 tracking-tight">İhracat & Evrak Takip Masası</h1>
                    <span class="bg-blue-100 text-blue-800 text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">Operasyon</span>
                </div>
                <p class="text-sm text-slate-500 mt-1">Yapılan ihracatların evrak durumu, cut-off süreleri ve gecikme uyarılarını buradan 7/24 izleyin.</p>
            </div>
            <div class="flex items-center space-x-3">
                <a href="{{ url_for('export_manager.admin_export_alerts') }}" class="relative inline-flex items-center space-x-2 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 font-bold px-4 py-2.5 rounded-xl shadow-sm transition text-sm">
                    <i class="fa-solid fa-bell animate-pulse"></i>
                    <span>Alarmlar & Uyarılar</span>
                    {% if total_alerts_count > 0 %}
                    <span class="bg-rose-600 text-white text-xs px-2 py-0.5 rounded-full font-extrabold">{{ total_alerts_count }}</span>
                    {% endif %}
                </a>
                <button onclick="document.getElementById('modal-new-export').classList.remove('hidden')" class="inline-flex items-center space-x-2 bg-[#0B3B60] hover:bg-sky-900 text-white font-bold px-4 py-2.5 rounded-xl shadow-md transition text-sm">
                    <i class="fa-solid fa-plus"></i>
                    <span>Yeni İhracat Dosyası Aç</span>
                </button>
            </div>
        </div>

        <!-- İstatistik KPI Kartları -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
                <div>
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Aktif İhracatlar</span>
                    <div class="text-3xl font-black text-slate-800 mt-1">{{ active_shipments_count }}</div>
                    <span class="text-xs text-sky-600 font-medium">Devam eden sevkiyat</span>
                </div>
                <div class="w-12 h-12 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center text-xl shadow-inner">
                    <i class="fa-solid fa-ship"></i>
                </div>
            </div>

            <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
                <div>
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Bekleyen Acil Evrak</span>
                    <div class="text-3xl font-black text-amber-600 mt-1">{{ urgent_tasks_count }}</div>
                    <span class="text-xs text-amber-600 font-medium">Onay/Yükleme bekliyor</span>
                </div>
                <div class="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center text-xl shadow-inner">
                    <i class="fa-solid fa-file-circle-exclamation"></i>
                </div>
            </div>

            <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
                <div>
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Aktif Alarmlar</span>
                    <div class="text-3xl font-black text-rose-600 mt-1">{{ total_alerts_count }}</div>
                    <span class="text-xs text-rose-600 font-medium">Geciken veya yaklaşan</span>
                </div>
                <div class="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center text-xl shadow-inner">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                </div>
            </div>

            <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
                <div>
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tamamlanan Dosyalar</span>
                    <div class="text-3xl font-black text-emerald-600 mt-1">{{ completed_shipments_count }}</div>
                    <span class="text-xs text-emerald-600 font-medium">Başarıyla teslim edildi</span>
                </div>
                <div class="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl shadow-inner">
                    <i class="fa-solid fa-circle-check"></i>
                </div>
            </div>
        </div>

        <!-- Filtre Sekmeleri & Arama -->
        <div class="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-3 rounded-2xl border border-slate-200/80 shadow-sm">
            <div class="flex items-center space-x-1.5 overflow-x-auto w-full sm:w-auto text-xs font-semibold">
                <a href="{{ url_for('export_manager.admin_exports', filter='all') }}" class="px-3.5 py-2 rounded-xl transition {{ 'bg-[#0B3B60] text-white shadow-sm' if filter_mode == 'all' else 'text-slate-600 hover:bg-slate-100' }}">Tümü</a>
                <a href="{{ url_for('export_manager.admin_exports', filter='active') }}" class="px-3.5 py-2 rounded-xl transition {{ 'bg-[#0B3B60] text-white shadow-sm' if filter_mode == 'active' else 'text-slate-600 hover:bg-slate-100' }}">Devam Edenler</a>
                <a href="{{ url_for('export_manager.admin_exports', filter='sea') }}" class="px-3.5 py-2 rounded-xl transition flex items-center space-x-1.5 {{ 'bg-[#0B3B60] text-white shadow-sm' if filter_mode == 'sea' else 'text-slate-600 hover:bg-slate-100' }}">
                    <i class="fa-solid fa-ship text-sky-500"></i><span>Denizyolu</span>
                </a>
                <a href="{{ url_for('export_manager.admin_exports', filter='road') }}" class="px-3.5 py-2 rounded-xl transition flex items-center space-x-1.5 {{ 'bg-[#0B3B60] text-white shadow-sm' if filter_mode == 'road' else 'text-slate-600 hover:bg-slate-100' }}">
                    <i class="fa-solid fa-truck text-amber-500"></i><span>Karayolu</span>
                </a>
                <a href="{{ url_for('export_manager.admin_exports', filter='completed') }}" class="px-3.5 py-2 rounded-xl transition {{ 'bg-[#0B3B60] text-white shadow-sm' if filter_mode == 'completed' else 'text-slate-600 hover:bg-slate-100' }}">Tamamlananlar</a>
            </div>

            <form method="GET" class="w-full sm:w-72">
                <div class="relative">
                    <input type="text" name="search" value="{{ search }}" placeholder="Dosya no, müşteri, ülke ara..." class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 focus:bg-white outline-none">
                    <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
                </div>
            </form>
        </div>

        <!-- Sevkiyat Kartları Listesi -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {% for s in shipments %}
            <div class="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between overflow-hidden relative group">
                <!-- Üst Şerit & Uyarı İndikatörü -->
                {% if s.has_alert %}
                <div class="bg-rose-500 text-white text-[11px] font-bold px-3 py-1 flex items-center justify-between tracking-wide animate-pulse">
                    <span><i class="fa-solid fa-triangle-exclamation mr-1.5"></i>Acil Aksiyon / Evrak Bekliyor!</span>
                    <a href="{{ url_for('export_manager.admin_export_alerts') }}" class="underline text-[10px]">İncele</a>
                </div>
                {% endif %}

                <div class="p-5 flex-1">
                    <!-- Kart Başlığı -->
                    <div class="flex items-start justify-between">
                        <div>
                            <span class="text-xs font-black tracking-wider text-blue-700 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-100">
                                {{ s.file_no }}
                            </span>
                            <h3 class="font-bold text-slate-900 text-base mt-2 leading-snug">{{ s.customer_name }}</h3>
                            <div class="flex items-center space-x-1.5 text-xs text-slate-500 mt-1">
                                <i class="fa-solid fa-location-dot text-rose-500"></i>
                                <span>{{ s.country }}</span>
                                {% if s.destination_port %}
                                <span>&bull; {{ s.destination_port }}</span>
                                {% endif %}
                            </div>
                        </div>

                        <!-- Taşıma Modu Rozeti -->
                        <div class="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center text-lg shadow-inner">
                            {% if s.transport_mode == 'sea' %}
                            <i class="fa-solid fa-ship text-sky-600" title="Denizyolu"></i>
                            {% elif s.transport_mode == 'road' %}
                            <i class="fa-solid fa-truck text-amber-600" title="Karayolu"></i>
                            {% else %}
                            <i class="fa-solid fa-plane text-violet-600" title="Havayolu"></i>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Operasyonel Detaylar -->
                    <div class="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-100 text-xs">
                        <div class="bg-slate-50 p-2 rounded-xl">
                            <span class="text-slate-400 text-[10px] uppercase font-bold block">Teslim Şekli</span>
                            <span class="font-bold text-slate-800">{{ s.incoterm }}</span>
                        </div>
                        <div class="bg-slate-50 p-2 rounded-xl">
                            <span class="text-slate-400 text-[10px] uppercase font-bold block">Durum</span>
                            {% if s.status == 'preparing' %}
                            <span class="font-bold text-amber-600">Hazırlıkta</span>
                            {% elif s.status == 'customs' %}
                            <span class="font-bold text-indigo-600">Gümrükte</span>
                            {% elif s.status == 'in_transit' %}
                            <span class="font-bold text-sky-600">Yolda</span>
                            {% elif s.status == 'delivered' %}
                            <span class="font-bold text-emerald-600">Ulaştı</span>
                            {% elif s.status == 'completed' %}
                            <span class="font-bold text-slate-600">Tamamlandı</span>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Kritik Tarihler -->
                    <div class="mt-3 space-y-1.5 text-xs text-slate-600">
                        {% if s.cutoff_datetime %}
                        <div class="flex items-center justify-between bg-amber-50/70 px-2 py-1 rounded-lg border border-amber-100 text-[11px]">
                            <span class="font-semibold text-amber-900"><i class="fa-regular fa-clock mr-1 text-amber-600"></i>Cut-Off:</span>
                            <span class="font-bold text-amber-950 font-mono">{{ s.cutoff_datetime }}</span>
                        </div>
                        {% endif %}
                        <div class="flex items-center justify-between text-[11px] text-slate-500 px-1">
                            <span>Kalkış (ETD): <strong class="text-slate-700">{{ s.etd or '-' }}</strong></span>
                            <span>Varış (ETA): <strong class="text-slate-700">{{ s.eta or '-' }}</strong></span>
                        </div>
                    </div>

                    <!-- Evrak İlerleme Durumu -->
                    <div class="mt-4 pt-3 border-t border-slate-100">
                        <div class="flex items-center justify-between text-xs font-semibold mb-1.5">
                            <span class="text-slate-600">Evrak & Görev Hazırlığı</span>
                            <span class="{{ 'text-emerald-600' if s.pct == 100 else 'text-blue-700' }} font-bold">{{ s.done_tasks }}/{{ s.total_tasks }} (%{{ s.pct }})</span>
                        </div>
                        <div class="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                            <div class="h-2.5 rounded-full transition-all duration-500 {{ 'bg-emerald-500' if s.pct == 100 else 'bg-blue-600' }}" style="width: {{ s.pct }}%"></div>
                        </div>
                    </div>
                </div>

                <!-- Kart Alt Aksiyonları -->
                <div class="bg-slate-50 px-5 py-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span class="text-slate-400 font-mono text-[11px]">{{ s.carrier_forwarder or 'Acente serbest' }}</span>
                    <a href="{{ url_for('export_manager.admin_export_detail', id=s.id) }}" class="inline-flex items-center space-x-1.5 bg-white border border-slate-200 hover:border-blue-500 hover:text-blue-600 text-slate-700 font-bold px-3 py-1.5 rounded-xl shadow-sm transition">
                        <span>Evrakları İncele</span>
                        <i class="fa-solid fa-arrow-right text-[10px]"></i>
                    </a>
                </div>
            </div>
            {% else %}
            <div class="col-span-full bg-white rounded-2xl p-12 text-center border border-slate-200">
                <i class="fa-solid fa-ship text-slate-300 text-5xl mb-3"></i>
                <h3 class="text-base font-bold text-slate-700">Kayıtlı ihracat dosyası bulunamadı</h3>
                <p class="text-xs text-slate-400 mt-1">Arama kriterlerinize uygun sevkiyat bulunamadı veya henüz dosya açılmadı.</p>
                <button onclick="document.getElementById('modal-new-export').classList.remove('hidden')" class="mt-4 inline-flex items-center space-x-2 bg-[#0B3B60] text-white text-xs font-bold px-4 py-2 rounded-xl">
                    <i class="fa-solid fa-plus"></i>
                    <span>İlk İhracatı Ekle</span>
                </button>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- MODAL: YENİ İHRACAT DOSYASI AÇMA -->
    <div id="modal-new-export" class="hidden fixed inset-0 z-50 bg-slate-950/50 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl max-w-xl w-full p-6 md:p-8 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between pb-4 border-b border-slate-100">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center text-lg">
                        <i class="fa-solid fa-file-circle-plus"></i>
                    </div>
                    <div>
                        <h2 class="text-lg font-bold text-slate-900">Yeni İhracat Dosyası Aç</h2>
                        <p class="text-xs text-slate-400">Sevkiyat oluşturulduğunda evrak kontrol listesi otomatik tanımlanır.</p>
                    </div>
                </div>
                <button onclick="document.getElementById('modal-new-export').classList.add('hidden')" class="text-slate-400 hover:text-slate-600 p-2">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
            </div>

            <form action="{{ url_for('export_manager.admin_export_add') }}" method="POST" class="space-y-4 mt-5">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Dosya / Ref No *</label>
                        <input type="text" name="file_no" required placeholder="Örn: EXP-2026-004" class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Müşteri / Alıcı Unvanı *</label>
                        <input type="text" name="customer_name" required placeholder="Örn: Cairo Medical Supplies" class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Hedef Ülke *</label>
                        <input type="text" name="country" required placeholder="Örn: Almanya, Mısır, Rusya" class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Hedef Liman / Şehir</label>
                        <input type="text" name="destination_port" placeholder="Örn: Hamburg Port / Münih" class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Taşıma Şekli</label>
                        <select name="transport_mode" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                            <option value="sea">🚢 Denizyolu</option>
                            <option value="road">🚛 Karayolu</option>
                            <option value="air">✈️ Havayolu</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Teslim Şekli (Incoterm)</label>
                        <select name="incoterm" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                            <option value="FOB">FOB</option>
                            <option value="CIF">CIF</option>
                            <option value="CFR">CFR</option>
                            <option value="EXW">EXW</option>
                            <option value="DAP">DAP</option>
                            <option value="CPT">CPT</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Nakliyeci / Acente</label>
                        <input type="text" name="carrier_forwarder" placeholder="Örn: Maersk, Ekol" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                    <div>
                        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Cut-off (Liman Kapanış)</label>
                        <input type="datetime-local" name="cutoff_datetime" class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Kalkış Tarihi (ETD)</label>
                        <input type="date" name="etd" class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Tahmini Varış (ETA)</label>
                        <input type="date" name="eta" class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Operasyon Notları</label>
                    <textarea name="notes" rows="2" placeholder="Konteyner tipi, özel müşteri talepleri, akreditif şartları..." class="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none"></textarea>
                </div>

                <div class="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
                    <button type="button" onclick="document.getElementById('modal-new-export').classList.add('hidden')" class="px-5 py-2.5 text-xs font-bold text-slate-500 hover:text-slate-800">Vazgeç</button>
                    <button type="submit" class="px-6 py-2.5 text-xs font-bold bg-[#0B3B60] hover:bg-sky-900 text-white rounded-xl shadow-md transition">Kaydet ve Kontrol Listesini Oluştur</button>
                </div>
            </form>
        </div>
    </div>
    """

    from server import BASE_LAYOUT, get_local_ip
    return render_template_string(
        BASE_LAYOUT.replace("{% block content %}{% endblock %}", content),
        title="İhracat Takip Masası",
        local_ip=get_local_ip(),
        shipments=shipment_list,
        active_shipments_count=active_shipments_count,
        total_alerts_count=total_alerts_count,
        urgent_tasks_count=urgent_tasks_count,
        completed_shipments_count=completed_shipments_count,
        filter_mode=filter_mode,
        search=search
    )


# ==================== İHRACAT DETAY VE EVRAK YÖNETİMİ ====================

@export_bp.route("/admin/exports/<int:id>")
def admin_export_detail(id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM export_shipments WHERE id = ?", (id,))
    shipment = cursor.fetchone()
    if not shipment:
        conn.close()
        flash("İhracat dosyası bulunamadı", "error")
        return redirect(url_for('export_manager.admin_exports'))

    cursor.execute("SELECT * FROM export_tasks WHERE shipment_id = ? ORDER BY is_completed ASC, priority = 'urgent' DESC, id ASC", (id,))
    tasks = cursor.fetchall()

    cursor.execute("SELECT * FROM export_alerts WHERE shipment_id = ? AND is_resolved = 0 ORDER BY id DESC", (id,))
    alerts = cursor.fetchall()

    # İlerleme hesabı
    total_t = len(tasks)
    done_t = sum(1 for t in tasks if t["is_completed"] == 1)
    pct = int((done_t / total_t * 100)) if total_t > 0 else 0

    conn.close()

    content = """
    <div class="space-y-6">
        <!-- Geri Butonu ve Başlık -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="flex items-center space-x-4">
                <a href="{{ url_for('export_manager.admin_exports') }}" class="w-10 h-10 rounded-2xl bg-white border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-400 flex items-center justify-center shadow-sm transition">
                    <i class="fa-solid fa-arrow-left"></i>
                </a>
                <div>
                    <div class="flex items-center space-x-2">
                        <span class="text-xs font-black tracking-wider text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-lg border border-blue-100">{{ s.file_no }}</span>
                        <h1 class="text-2xl font-black text-slate-800">{{ s.customer_name }}</h1>
                    </div>
                    <p class="text-xs text-slate-500 mt-0.5"><i class="fa-solid fa-location-dot text-rose-500 mr-1"></i>{{ s.country }} {% if s.destination_port %}&bull; {{ s.destination_port }}{% endif %}</p>
                </div>
            </div>

            <!-- Durum Güncelleme ve Aksiyonlar -->
            <div class="flex items-center space-x-3">
                <form action="{{ url_for('export_manager.admin_export_status', id=s.id) }}" method="POST" class="flex items-center space-x-2">
                    <select name="status" onchange="this.form.submit()" class="bg-white border border-slate-200 text-xs font-bold rounded-xl px-3 py-2 shadow-sm outline-none text-slate-700 focus:ring-2 focus:ring-blue-500">
                        <option value="preparing" {{ 'selected' if s.status == 'preparing' }}>🟡 Hazırlık Aşamasında</option>
                        <option value="customs" {{ 'selected' if s.status == 'customs' }}>🟣 Gümrükleme / Tescil</option>
                        <option value="in_transit" {{ 'selected' if s.status == 'in_transit' }}>🔵 Yolda / Seyir Halinde</option>
                        <option value="delivered" {{ 'selected' if s.status == 'delivered' }}>🟢 Varış / Teslim Edildi</option>
                        <option value="completed" {{ 'selected' if s.status == 'completed' }}>✅ Dosya Kapandı / Tamamlandı</option>
                    </select>
                </form>

                <button onclick="document.getElementById('modal-add-task').classList.remove('hidden')" class="inline-flex items-center space-x-2 bg-[#0B3B60] hover:bg-sky-900 text-white text-xs font-bold px-3.5 py-2 rounded-xl shadow-sm transition">
                    <i class="fa-solid fa-plus"></i>
                    <span>Özel Evrak Ekle</span>
                </button>
            </div>
        </div>

        <!-- Aktif Alarmlar Varsa Üst Şerit -->
        {% if alerts %}
        <div class="bg-rose-50 border border-rose-200 rounded-2xl p-4 space-y-2">
            <div class="flex items-center space-x-2 text-rose-800 font-bold text-xs">
                <i class="fa-solid fa-triangle-exclamation text-rose-600 animate-pulse text-sm"></i>
                <span>Bu sevkiyatta dikkat edilmesi gereken kritik uyarılar var:</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {% for a in alerts %}
                <div class="bg-white p-3 rounded-xl border border-rose-200/80 shadow-xs flex items-start justify-between">
                    <div>
                        <div class="font-bold text-xs text-rose-900">{{ a.title }}</div>
                        <div class="text-[11px] text-slate-600 mt-0.5">{{ a.message }}</div>
                    </div>
                    <form action="{{ url_for('export_manager.admin_alert_resolve', id=a.id) }}" method="POST">
                        <button type="submit" class="text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded-lg font-bold">Kapat</button>
                    </form>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <!-- Sevkiyat Bilgi Özeti & İlerleme Kartı -->
        <div class="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div class="space-y-2">
                <span class="text-slate-400 text-[10px] font-bold uppercase tracking-wider block">Lojistik & Taşıma</span>
                <div class="flex items-center space-x-2 text-sm font-bold text-slate-800">
                    {% if s.transport_mode == 'sea' %}<i class="fa-solid fa-ship text-sky-600"></i> Denizyolu
                    {% elif s.transport_mode == 'road' %}<i class="fa-solid fa-truck text-amber-600"></i> Karayolu
                    {% else %}<i class="fa-solid fa-plane text-violet-600"></i> Havayolu{% endif %}
                    <span>&bull; {{ s.incoterm }}</span>
                </div>
                <div class="text-xs text-slate-500 font-mono">{{ s.carrier_forwarder or 'Acente serbest' }}</div>
            </div>

            <div class="space-y-1 text-xs">
                <span class="text-slate-400 text-[10px] font-bold uppercase tracking-wider block">Kritik Tarihler</span>
                <div>Cut-Off: <strong class="text-amber-900 font-mono">{{ s.cutoff_datetime or 'Belirtilmedi' }}</strong></div>
                <div>Kalkış (ETD): <strong class="text-slate-700 font-mono">{{ s.etd or '-' }}</strong></div>
                <div>Varış (ETA): <strong class="text-slate-700 font-mono">{{ s.eta or '-' }}</strong></div>
            </div>

            <div class="space-y-1 text-xs">
                <span class="text-slate-400 text-[10px] font-bold uppercase tracking-wider block">Dosya Notları</span>
                <p class="text-slate-600 line-clamp-3 italic">{{ s.notes or 'Özel operasyon notu eklenmedi.' }}</p>
            </div>

            <div class="flex flex-col justify-center bg-slate-50 p-4 rounded-2xl border border-slate-100">
                <div class="flex items-center justify-between text-xs font-bold mb-1">
                    <span class="text-slate-600">Evrak Tamamlanma</span>
                    <span class="{{ 'text-emerald-600' if pct == 100 else 'text-blue-700' }}">{{ done_t }}/{{ total_t }} (%{{ pct }})</span>
                </div>
                <div class="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                    <div class="h-3 rounded-full transition-all duration-500 {{ 'bg-emerald-500' if pct == 100 else 'bg-blue-600' }}" style="width: {{ pct }}%"></div>
                </div>
                <span class="text-[10px] text-slate-400 mt-2 text-center">Tüm evraklar yüklenip onaylandığında dosya kapanır.</span>
            </div>
        </div>

        <!-- Evrak & Görev Kontrol Listesi (Interactive Checklist Matrix) -->
        <div class="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="p-6 border-b border-slate-100 flex items-center justify-between">
                <div>
                    <h2 class="text-lg font-black text-slate-900">Evrak & Görev Kontrol Matrisi</h2>
                    <p class="text-xs text-slate-400">Tek tıkla evrak durumunu değiştirebilir, PDF yükleyebilir ve takip kodu girebilirsiniz.</p>
                </div>
                <span class="text-xs text-slate-400 font-mono">{{ total_t }} Görev Kayıtlı</span>
            </div>

            <div class="divide-y divide-slate-100">
                {% for t in tasks %}
                <div class="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/80 transition {{ 'bg-emerald-50/30' if t.is_completed else '' }}">
                    <div class="flex items-start space-x-3.5 flex-1">
                        <!-- Toggle Checkbox -->
                        <form action="{{ url_for('export_manager.admin_task_toggle', id=t.id) }}" method="POST" class="mt-0.5">
                            <button type="submit" class="w-7 h-7 rounded-xl flex items-center justify-center transition shadow-xs {{ 'bg-emerald-500 text-white hover:bg-emerald-600' if t.is_completed else 'bg-slate-100 border border-slate-300 text-transparent hover:text-slate-400' }}">
                                <i class="fa-solid fa-check text-xs"></i>
                            </button>
                        </form>

                        <div class="space-y-1 flex-1">
                            <div class="flex items-center space-x-2">
                                <span class="font-bold text-sm {{ 'line-through text-slate-400' if t.is_completed else 'text-slate-900' }}">{{ t.title }}</span>
                                
                                {% if t.priority == 'urgent' and not t.is_completed %}
                                <span class="bg-rose-100 text-rose-700 text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider">Acil</span>
                                {% endif %}

                                <span class="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono uppercase">
                                    {% if t.category == 'document' %}Evrak
                                    {% elif t.category == 'transport' %}Lojistik
                                    {% elif t.category == 'customs' %}Gümrük
                                    {% elif t.category == 'courier' %}Kargo
                                    {% else %}Finans{% endif %}
                                </span>
                            </div>

                            {% if t.notes %}
                            <p class="text-xs text-slate-500">{{ t.notes }}</p>
                            {% endif %}

                            <div class="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-1">
                                {% if t.due_datetime %}
                                <span><i class="fa-regular fa-calendar-clock mr-1 text-slate-400"></i>Son: <strong class="text-slate-700 font-mono">{{ t.due_datetime }}</strong></span>
                                {% endif %}

                                {% if t.tracking_code %}
                                <span class="text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100 font-mono font-bold">
                                    <i class="fa-solid fa-truck-fast mr-1"></i>Takip: {{ t.tracking_code }}
                                </span>
                                {% endif %}

                                {% if t.is_completed and t.completed_at %}
                                <span class="text-emerald-700"><i class="fa-solid fa-check-double mr-1"></i>{{ t.completed_at }} tamamlandı</span>
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <!-- Sağ Taraf: Belge Yükleme / İndirme / Takip No Girişi -->
                    <div class="flex items-center space-x-2 text-xs">
                        {% if t.document_file_url %}
                        <a href="{{ t.document_file_url }}" target="_blank" class="inline-flex items-center space-x-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold px-3 py-1.5 rounded-xl border border-blue-200 transition">
                            <i class="fa-solid fa-file-arrow-down"></i>
                            <span>Belgeyi Aç / İndir</span>
                        </a>
                        {% endif %}

                        <button onclick="openUploadModal('{{ t.id }}', '{{ t.title }}')" class="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold transition" title="Belge PDF Yükle veya Takip Kodu Ekle">
                            <i class="fa-solid fa-paperclip"></i>
                        </button>

                        <form action="{{ url_for('export_manager.admin_task_delete', id=t.id) }}" method="POST" onsubmit="return confirm('Bu görevi silmek istediğinize emin misiniz?');">
                            <button type="submit" class="p-2 rounded-xl text-slate-400 hover:text-rose-600 transition" title="Görevi Sil">
                                <i class="fa-solid fa-trash-can"></i>
                            </button>
                        </form>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- MODAL: BELGE YÜKLEME & TAKİP NO GİRİŞİ -->
    <div id="modal-upload" class="hidden fixed inset-0 z-50 bg-slate-950/50 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 class="font-bold text-slate-900 text-sm" id="modal-upload-title">Evrak / Takip Bilgisi Ekle</h3>
                <button onclick="document.getElementById('modal-upload').classList.add('hidden')" class="text-slate-400 hover:text-slate-600 p-1"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <form id="upload-form" action="" method="POST" enctype="multipart/form-data" class="space-y-4 mt-4 text-xs">
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Evrak Dosyası (PDF / Resim)</label>
                    <input type="file" name="doc_file" accept=".pdf,.png,.jpg,.jpeg,.xlsx" class="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Kargo Takip No (Varsa)</label>
                    <input type="text" name="tracking_code" placeholder="Örn: DHL 123456789, FedEx 987654" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Not Ekle</label>
                    <input type="text" name="notes" placeholder="Belge hakkında not..." class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
                </div>
                <div class="pt-3 border-t border-slate-100 flex justify-end space-x-2">
                    <button type="button" onclick="document.getElementById('modal-upload').classList.add('hidden')" class="px-4 py-2 font-bold text-slate-500">Vazgeç</button>
                    <button type="submit" class="px-5 py-2 font-bold bg-[#0B3B60] text-white rounded-xl shadow transition">Kaydet</button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL: YENİ ÖZEL GÖREV / EVRAK EKLE -->
    <div id="modal-add-task" class="hidden fixed inset-0 z-50 bg-slate-950/50 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 class="font-bold text-slate-900 text-sm">Bu Sevkiyata Özel Evrak/Görev Ekle</h3>
                <button onclick="document.getElementById('modal-add-task').classList.add('hidden')" class="text-slate-400 hover:text-slate-600 p-1"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <form action="{{ url_for('export_manager.admin_task_add', shipment_id=s.id) }}" method="POST" class="space-y-4 mt-4 text-xs">
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Evrak / Görev Başlığı *</label>
                    <input type="text" name="title" required placeholder="Örn: Sağlık Bakanlığı İzin Belgesi" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-none">
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block font-bold text-slate-700 mb-1">Kategori</label>
                        <select name="category" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
                            <option value="document">📄 Evrak</option>
                            <option value="customs">🏛️ Gümrük</option>
                            <option value="transport">🚢 Lojistik</option>
                            <option value="payment">💳 Finans</option>
                            <option value="courier">📦 Kargo</option>
                        </select>
                    </div>
                    <div>
                        <label class="block font-bold text-slate-700 mb-1">Öncelik</label>
                        <select name="priority" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
                            <option value="normal">Normal</option>
                            <option value="urgent">🚨 Acil</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Son Yapılma Zamanı (Deadline)</label>
                    <input type="datetime-local" name="due_datetime" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Not / Açıklama</label>
                    <input type="text" name="notes" placeholder="Görevle ilgili kısa açıklama..." class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
                </div>
                <div class="pt-3 border-t border-slate-100 flex justify-end space-x-2">
                    <button type="button" onclick="document.getElementById('modal-add-task').classList.add('hidden')" class="px-4 py-2 font-bold text-slate-500">Vazgeç</button>
                    <button type="submit" class="px-5 py-2 font-bold bg-[#0B3B60] text-white rounded-xl shadow transition">Görevi Ekle</button>
                </div>
            </form>
        </div>
    </div>

    <script>
    function openUploadModal(taskId, title) {
        document.getElementById('modal-upload-title').innerText = title + ' - Evrak / Takip Ekle';
        document.getElementById('upload-form').action = '/admin/exports/task/' + taskId + '/upload';
        document.getElementById('modal-upload').classList.remove('hidden');
    }
    </script>
    """

    from server import BASE_LAYOUT, get_local_ip
    return render_template_string(
        BASE_LAYOUT.replace("{% block content %}{% endblock %}", content),
        title=f"{shipment['file_no']} - Evrak Takip",
        local_ip=get_local_ip(),
        s=shipment,
        tasks=tasks,
        alerts=alerts,
        total_t=total_t,
        done_t=done_t,
        pct=pct
    )


# ==================== ALARMLAR VE AKILLI BİLDİRİM MERKEZİ ====================

@export_bp.route("/admin/exports/alerts")
def admin_export_alerts():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.*, s.file_no, s.customer_name, s.country 
        FROM export_alerts a
        LEFT JOIN export_shipments s ON a.shipment_id = s.id
        WHERE a.is_resolved = 0
        ORDER BY a.severity = 'danger' DESC, a.id DESC
    """)
    alerts = cursor.fetchall()

    cursor.execute("SELECT key, value FROM export_settings")
    settings = dict(cursor.fetchall())
    conn.close()

    content = """
    <div class="space-y-6">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <div class="flex items-center space-x-3">
                    <h1 class="text-2xl font-black text-slate-800 tracking-tight">Akıllı Bildirim & Uyarı Merkezi</h1>
                    <span class="bg-rose-100 text-rose-800 text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">Otomasyon</span>
                </div>
                <p class="text-sm text-slate-500 mt-1">Sistem, ihracatlarınızın cut-off sürelerini, eksik evraklarını ve kargolanmamış belgelerini düzenli olarak denetler.</p>
            </div>
            <div class="flex items-center space-x-3">
                <form action="{{ url_for('export_manager.admin_trigger_check') }}" method="POST">
                    <button type="submit" class="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2.5 rounded-xl shadow transition text-sm">
                        <i class="fa-solid fa-rotate"></i>
                        <span>Şimdi Kuralları Çalıştır & Alarmları Yenile</span>
                    </button>
                </form>
            </div>
        </div>

        <!-- Telegram Entegrasyon Kutusu -->
        <div class="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-2xl bg-sky-500 text-white flex items-center justify-center text-xl shadow-md">
                        <i class="fa-brands fa-telegram"></i>
                    </div>
                    <div>
                        <h2 class="font-bold text-slate-900 text-base">Telegram Cep Bildirim Botu Entegrasyonu</h2>
                        <p class="text-xs text-slate-500">Unutulan evraklar ve cut-off uyarıları anında cebinize Telegram mesajı olarak gelsin.</p>
                    </div>
                </div>
            </div>

            <form action="{{ url_for('export_manager.admin_save_telegram_settings') }}" method="POST" class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Telegram Bot Token</label>
                    <input type="text" name="bot_token" value="{{ settings.get('telegram_bot_token', '') }}" placeholder="Örn: 7123456789:AAHx..." class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none font-mono">
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Telegram Chat ID</label>
                    <input type="text" name="chat_id" value="{{ settings.get('telegram_chat_id', '') }}" placeholder="Örn: 987654321" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none font-mono">
                </div>
                <div class="flex items-end space-x-2">
                    <button type="submit" class="px-4 py-2 bg-[#0B3B60] hover:bg-sky-900 text-white font-bold rounded-xl shadow transition">Kaydet</button>
                    <button type="submit" name="test_msg" value="1" class="px-4 py-2 bg-sky-100 hover:bg-sky-200 text-sky-800 font-bold rounded-xl transition">Test Mesajı Gönder</button>
                </div>
            </form>
        </div>

        <!-- Aktif Alarmlar Listesi -->
        <div class="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="p-6 border-b border-slate-100 flex items-center justify-between">
                <div>
                    <h2 class="text-lg font-black text-slate-900">Müdahale Bekleyen Alarmlar</h2>
                    <p class="text-xs text-slate-400">Herhangi bir alarm için aksiyon aldığınızda kapatabilir veya erteleyebilirsiniz.</p>
                </div>
                <span class="text-xs font-bold px-3 py-1 bg-rose-50 text-rose-700 border border-rose-100 rounded-full">{{ alerts|length }} Aktif Alarm</span>
            </div>

            <div class="divide-y divide-slate-100">
                {% for a in alerts %}
                <div class="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 {{ 'bg-rose-50/40' if a.severity == 'danger' else 'bg-amber-50/30' }}">
                    <div class="flex items-start space-x-3.5 flex-1">
                        <div class="w-10 h-10 rounded-2xl flex items-center justify-center text-lg flex-shrink-0 {{ 'bg-rose-100 text-rose-600' if a.severity == 'danger' else 'bg-amber-100 text-amber-600' }}">
                            {% if a.alert_type == 'cutoff_approaching' %}<i class="fa-regular fa-clock"></i>
                            {% elif a.alert_type == 'overdue_task' %}<i class="fa-solid fa-circle-exclamation"></i>
                            {% elif a.alert_type == 'courier_missing' %}<i class="fa-solid fa-box-open"></i>
                            {% else %}<i class="fa-solid fa-triangle-exclamation"></i>{% endif %}
                        </div>

                        <div class="space-y-1">
                            <div class="flex items-center space-x-2">
                                <span class="font-bold text-sm text-slate-900">{{ a.title }}</span>
                                <span class="text-[10px] font-mono bg-white border border-slate-200 text-slate-600 px-2 py-0.5 rounded font-bold">{{ a.file_no }}</span>
                            </div>
                            <p class="text-xs text-slate-600 leading-relaxed">{{ a.message }}</p>
                            <span class="text-[10px] text-slate-400 block pt-1"><i class="fa-regular fa-calendar mr-1"></i>{{ a.created_at }} tespit edildi</span>
                        </div>
                    </div>

                    <!-- Aksiyon Butonları -->
                    <div class="flex items-center space-x-2 text-xs">
                        <a href="{{ url_for('export_manager.admin_export_detail', id=a.shipment_id) }}" class="px-3.5 py-2 bg-white border border-slate-200 hover:border-blue-500 hover:text-blue-700 text-slate-700 font-bold rounded-xl shadow-xs transition">
                            <i class="fa-solid fa-file-lines mr-1"></i>Dosyaya Git
                        </a>

                        <!-- 1 Gün Ertele -->
                        <form action="{{ url_for('export_manager.admin_alert_snooze', id=a.id, hours=24) }}" method="POST">
                            <button type="submit" class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition" title="24 Saat Ertele">
                                <i class="fa-regular fa-clock mr-1"></i>1 Gün Ertele
                            </button>
                        </form>

                        <!-- Kapat / Çözüldü -->
                        <form action="{{ url_for('export_manager.admin_alert_resolve', id=a.id) }}" method="POST">
                            <button type="submit" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow transition">
                                <i class="fa-solid fa-check mr-1"></i>Kapat
                            </button>
                        </form>
                    </div>
                </div>
                {% else %}
                <div class="p-12 text-center text-slate-400">
                    <i class="fa-solid fa-shield-check text-emerald-500 text-5xl mb-3"></i>
                    <h3 class="font-bold text-slate-700 text-base">Harika! Bekleyen Kritik Bir Alarm Yok</h3>
                    <p class="text-xs text-slate-400 mt-1">Tüm ihracat evrakları ve cut-off süreleri planlanan takvimde ilerliyor.</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    """

    from server import BASE_LAYOUT, get_local_ip
    return render_template_string(
        BASE_LAYOUT.replace("{% block content %}{% endblock %}", content),
        title="İhracat Alarmları & Bildirimler",
        local_ip=get_local_ip(),
        alerts=alerts,
        settings=settings
    )


# ==================== AKSİYON ROUTE'LARI ====================

@export_bp.route("/admin/exports/add", methods=["POST"])
def admin_export_add():
    conn = get_db()
    cursor = conn.cursor()
    
    file_no = request.form.get("file_no", "").strip()
    customer_name = request.form.get("customer_name", "").strip()
    country = request.form.get("country", "").strip()
    destination_port = request.form.get("destination_port", "").strip()
    incoterm = request.form.get("incoterm", "FOB")
    transport_mode = request.form.get("transport_mode", "sea")
    carrier_forwarder = request.form.get("carrier_forwarder", "").strip()
    cutoff_datetime = request.form.get("cutoff_datetime") or None
    etd = request.form.get("etd") or None
    eta = request.form.get("eta") or None
    notes = request.form.get("notes", "").strip()

    try:
        cursor.execute("""
        INSERT INTO export_shipments (file_no, customer_name, country, destination_port, incoterm, transport_mode, carrier_forwarder, cutoff_datetime, etd, eta, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'preparing')
        """, (file_no, customer_name, country, destination_port, incoterm, transport_mode, carrier_forwarder, cutoff_datetime, etd, eta, notes))
        shipment_id = cursor.lastrowid
        conn.commit()

        # Standart görevleri ekle
        create_default_tasks_for_shipment(conn, shipment_id, transport_mode, incoterm, cutoff_datetime, etd)
        
        flash("İhracat dosyası ve evrak kontrol listesi oluşturuldu", "success")
        conn.close()
        return redirect(url_for('export_manager.admin_export_detail', id=shipment_id))
    except Exception as e:
        conn.close()
        flash(f"Hata: {e}", "error")
        return redirect(url_for('export_manager.admin_exports'))

@export_bp.route("/admin/exports/<int:id>/status", methods=["POST"])
def admin_export_status(id):
    conn = get_db()
    status = request.form.get("status", "preparing")
    conn.execute("UPDATE export_shipments SET status = ? WHERE id = ?", (status, id))
    conn.commit()
    conn.close()
    return redirect(url_for('export_manager.admin_export_detail', id=id))

@export_bp.route("/admin/exports/task/<int:id>/toggle", methods=["POST"])
def admin_task_toggle(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT shipment_id, is_completed FROM export_tasks WHERE id = ?", (id,))
    task = cursor.fetchone()
    if task:
        new_state = 0 if task["is_completed"] == 1 else 1
        comp_at = datetime.now().strftime('%Y-%m-%d %H:%M') if new_state == 1 else None
        cursor.execute("UPDATE export_tasks SET is_completed = ?, completed_at = ? WHERE id = ?", (new_state, comp_at, id))
        
        # Eğer tamamlandıysa bu göreve ait bekleyen alarmları çöz
        if new_state == 1:
            cursor.execute("UPDATE export_alerts SET is_resolved = 1 WHERE task_id = ?", (id,))
            
        conn.commit()
        shipment_id = task["shipment_id"]
        conn.close()
        return redirect(url_for('export_manager.admin_export_detail', id=shipment_id))
    conn.close()
    return redirect(url_for('export_manager.admin_exports'))

@export_bp.route("/admin/exports/task/<int:id>/upload", methods=["POST"])
def admin_task_upload(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT shipment_id FROM export_tasks WHERE id = ?", (id,))
    task = cursor.fetchone()
    if not task:
        conn.close()
        return redirect(url_for('export_manager.admin_exports'))

    shipment_id = task["shipment_id"]
    tracking_code = request.form.get("tracking_code", "").strip()
    notes = request.form.get("notes", "").strip()

    file = request.files.get("doc_file")
    filename = None
    if file and file.filename and allowed_doc_file(file.filename):
        filename = secure_filename(f"doc_{shipment_id}_{id}_{int(datetime.now().timestamp())}_{file.filename}")
        file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))

    if filename:
        cursor.execute("UPDATE export_tasks SET document_file_url = ?, is_completed = 1, completed_at = ? WHERE id = ?",
                       (make_doc_url(filename), datetime.now().strftime('%Y-%m-%d %H:%M'), id))
        cursor.execute("UPDATE export_alerts SET is_resolved = 1 WHERE task_id = ?", (id,))

    if tracking_code:
        cursor.execute("UPDATE export_tasks SET tracking_code = ? WHERE id = ?", (tracking_code, id))

    if notes:
        cursor.execute("UPDATE export_tasks SET notes = ? WHERE id = ?", (notes, id))

    conn.commit()
    conn.close()
    return redirect(url_for('export_manager.admin_export_detail', id=shipment_id))

@export_bp.route("/admin/exports/<int:shipment_id>/task/add", methods=["POST"])
def admin_task_add(shipment_id):
    conn = get_db()
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "document")
    priority = request.form.get("priority", "normal")
    due_datetime = request.form.get("due_datetime") or None
    notes = request.form.get("notes", "").strip()

    if title:
        conn.execute("""
        INSERT INTO export_tasks (shipment_id, title, category, priority, due_datetime, notes, is_completed)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (shipment_id, title, category, priority, due_datetime, notes))
        conn.commit()

    conn.close()
    return redirect(url_for('export_manager.admin_export_detail', id=shipment_id))

@export_bp.route("/admin/exports/task/<int:id>/delete", methods=["POST"])
def admin_task_delete(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT shipment_id FROM export_tasks WHERE id = ?", (id,))
    task = cursor.fetchone()
    shipment_id = task["shipment_id"] if task else None
    if task:
        cursor.execute("DELETE FROM export_tasks WHERE id = ?", (id,))
        cursor.execute("DELETE FROM export_alerts WHERE task_id = ?", (id,))
        conn.commit()
    conn.close()
    if shipment_id:
        return redirect(url_for('export_manager.admin_export_detail', id=shipment_id))
    return redirect(url_for('export_manager.admin_exports'))

@export_bp.route("/admin/exports/alerts/<int:id>/resolve", methods=["POST"])
def admin_alert_resolve(id):
    conn = get_db()
    conn.execute("UPDATE export_alerts SET is_resolved = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for('export_manager.admin_export_alerts'))

@export_bp.route("/admin/exports/alerts/<int:id>/snooze/<int:hours>", methods=["POST"])
def admin_alert_snooze(id, hours):
    conn = get_db()
    snooze_until = (datetime.now() + timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M')
    conn.execute("UPDATE export_alerts SET snooze_until = ? WHERE id = ?", (snooze_until, id))
    conn.commit()
    conn.close()
    return redirect(url_for('export_manager.admin_export_alerts'))

@export_bp.route("/admin/exports/alerts/trigger_check", methods=["POST"])
def admin_trigger_check():
    conn = get_db()
    run_export_rule_engine(conn, force=True)
    conn.close()
    flash("Kurallar çalıştırıldı ve uyarılar yenilendi.", "success")
    return redirect(url_for('export_manager.admin_export_alerts'))

@export_bp.route("/admin/exports/settings/telegram", methods=["POST"])
def admin_save_telegram_settings():
    conn = get_db()
    token = request.form.get("bot_token", "").strip()
    chat_id = request.form.get("chat_id", "").strip()

    conn.execute("INSERT OR REPLACE INTO export_settings (key, value) VALUES ('telegram_bot_token', ?)", (token,))
    conn.execute("INSERT OR REPLACE INTO export_settings (key, value) VALUES ('telegram_chat_id', ?)", (chat_id,))
    conn.commit()

    if request.form.get("test_msg") == "1" and token and chat_id:
        res = send_telegram_msg(token, chat_id, "🔔 *Betasan İhracat Asistanı Test Bildirimi*\n\nTelegram entegrasyonu başarıyla sağlandı! Unutulan evraklar ve cut-off süreleri için buradan anlık mesaj alacaksınız.")
        if res.get("ok"):
            flash("Telegram test mesajı başarıyla cep telefonunuza iletildi!", "success")
        else:
            flash(f"Telegram hatası: {res.get('error')}", "error")

    conn.close()
    return redirect(url_for('export_manager.admin_export_alerts'))


# ==================== JSON REST API ENDPOINT'LERİ (MOBİL / PWA ENTEGRASYONU) ====================

@export_bp.route("/api/exports", methods=["GET"])
def api_get_exports():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM export_shipments ORDER BY id DESC")
    shipments = cursor.fetchall()
    
    data = []
    for s in shipments:
        cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as done FROM export_tasks WHERE shipment_id = ?", (s["id"],))
        stat = cursor.fetchone()
        t_total = stat["total"] or 0
        t_done = stat["done"] or 0
        
        cursor.execute("SELECT COUNT(*) FROM export_alerts WHERE shipment_id = ? AND is_resolved = 0", (s["id"],))
        alert_count = cursor.fetchone()[0]

        data.append({
            "id": s["id"],
            "file_no": s["file_no"],
            "customer_name": s["customer_name"],
            "country": s["country"],
            "destination_port": s["destination_port"],
            "incoterm": s["incoterm"],
            "transport_mode": s["transport_mode"],
            "carrier_forwarder": s["carrier_forwarder"],
            "cutoff_datetime": s["cutoff_datetime"],
            "etd": s["etd"],
            "eta": s["eta"],
            "status": s["status"],
            "total_tasks": t_total,
            "done_tasks": t_done,
            "has_alerts": alert_count > 0,
            "alert_count": alert_count
        })
    conn.close()
    return jsonify({"success": True, "data": data})

@export_bp.route("/api/exports/<int:id>", methods=["GET"])
def api_get_export_detail(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM export_shipments WHERE id = ?", (id,))
    s = cursor.fetchone()
    if not s:
        conn.close()
        return jsonify({"success": False, "message": "İhracat dosyası bulunamadı"}), 404

    cursor.execute("SELECT * FROM export_tasks WHERE shipment_id = ? ORDER BY id ASC", (id,))
    tasks = [dict(t) for t in cursor.fetchall()]

    cursor.execute("SELECT * FROM export_alerts WHERE shipment_id = ? AND is_resolved = 0", (id,))
    alerts = [dict(a) for a in cursor.fetchall()]

    conn.close()
    return jsonify({
        "success": True,
        "shipment": dict(s),
        "tasks": tasks,
        "alerts": alerts
    })

@export_bp.route("/api/exports/check_alerts", methods=["POST"])
def api_check_alerts():
    conn = get_db()
    alerts = run_export_rule_engine(conn, force=True)
    conn.close()
    return jsonify({"success": True, "new_alerts": alerts, "count": len(alerts)})
