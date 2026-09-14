import os
import sys
import socket
import sqlite3
import webbrowser
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, send_from_directory, flash

app = Flask(__name__)
app.config["SECRET_KEY"] = "betasan-secret-2026"

try:
    from export_manager import export_bp, init_export_db
    app.register_blueprint(export_bp)
except Exception as e:
    print(f"Warning: Could not register export_bp: {e}")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "betasan.db")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    from db_adapter import get_universal_db
    return get_universal_db(DB_PATH)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT,
        icon TEXT,
        sort_order INTEGER DEFAULT 0
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT,
        category_id INTEGER,
        description TEXT,
        image TEXT,
        discount_rate INTEGER DEFAULT 0,
        is_featured INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS banners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subtitle TEXT,
        image TEXT,
        badge TEXT,
        product_id INTEGER,
        is_active INTEGER DEFAULT 1
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        target_product_id INTEGER,
        notif_type TEXT DEFAULT 'kampanya',
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS device_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE,
        device_type TEXT DEFAULT 'android',
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        customer_phone TEXT,
        items_json TEXT,
        note TEXT,
        channel TEXT DEFAULT 'whatsapp',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed categories if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cats = [
            ("Tıbbi Flasterler", "tibbi-flasterler", "bandage", 1),
            ("Fiksasyon Bantları", "fiksasyon-bantlari", "tape", 2),
            ("Enjeksiyon & Kan Alma", "enjeksiyon-kan-alma", "syringe", 3),
            ("Yara Bakım & Gazlı Bez", "yara-bakim", "cross", 4),
            ("İlk Yardım & Destek", "ilk-yardim", "heart-pulse", 5)
        ]
        cursor.executemany("INSERT INTO categories (name, slug, icon, sort_order) VALUES (?, ?, ?, ?)", cats)

    # Seed products if empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        prods = [
            ("Betaban İpek Tıbbi Flaster 5m x 5cm", "BT-101", 1, "Cilt dostu çinko oksit yapışkanı ve ipek dokusu ile hassas pansuman sabitlemeleri için idealdir. Enine ve boyuna kolay yırtılır.", None, 15, 1, 1),
            ("Betafix Elastik Tıbbi Fiksasyon Bandı 10m x 10cm", "BF-205", 2, "Hava geçirgen, esnek non-woven kumaş yapısıyla hareketli eklem bölgelerinde ve kateter sabitlemede güvenli tutuş sağlar.", None, 20, 1, 1),
            ("Betaseri Yuvarlak Enjeksiyon Bandı (100'lü)", "BS-310", 3, "Aşı, kan alma ve enjeksiyon sonrası kanamayı durdurmak için emici pedli, hipoalerjenik tek kullanımlık yuvarlak enjeksiyon bandı.", None, 0, 1, 1),
            ("Betaplast PU Su Geçirmez Şeffaf Film Flaster 10m x 5cm", "BP-404", 1, "Su geçirmez ve bakteri bariyeri oluşturan poliüretan film. Pansumanın ıslanmasını önler.", None, 10, 1, 1),
            ("Betasorb Steril Gaz Kompres 7.5cm x 7.5cm (50'li)", "BG-501", 4, "Yüksek sıvı emiciliğine sahip %100 saf pamuk hidrofil gaz kompres. Tek tek steril paketlidir.", None, 0, 0, 1),
            ("Betaderm Hassas Cerrahi Kağıt Flaster 5m x 2.5cm", "BD-602", 1, "Bebek, yaşlı ve hassas ciltler için mikrogözenekli hava geçiren kağıt flaster.", None, 25, 1, 1),
            ("Betasport Elastik Kendinden Yapışkanlı Koheziv Bandaj", "BK-808", 5, "Tene ve kıllara yapışmayan, sadece kendi üzerine tutunan elastik tespit ve kompresyon bandajı.", None, 15, 1, 1)
        ]
        cursor.executemany("INSERT INTO products (name, code, category_id, description, image, discount_rate, is_featured, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", prods)

    # Seed banners if empty
    cursor.execute("SELECT COUNT(*) FROM banners")
    if cursor.fetchone()[0] == 0:
        bans = [
            ("Yeni Nesil İpek Flasterler", "Hassas ciltler için üstün tutunma ve nefes alan doku", None, "%15 İndirim", 1, 1),
            ("Kurumsal Toplu Alım Avantajı", "Hastanelere ve kliniklere özel sepet teklif fırsatları", None, "Özel Fırsat", 2, 1)
        ]
        cursor.executemany("INSERT INTO banners (title, subtitle, image, badge, product_id, is_active) VALUES (?, ?, ?, ?, ?, ?)", bans)

    # Seed notification if empty
    cursor.execute("SELECT COUNT(*) FROM notifications")
    if cursor.fetchone()[0] == 0:
        notifs = [
            ("Yeni Nesil İpek Flasterler Satışta!", "Hassas ciltler için geliştirilen Betaban İpek Flaster serimiz kataloğa eklendi. Sepetinize ekleyip teklif alabilirsiniz.", 1, "kampanya"),
            ("Betafix Fiksasyon Bantlarında %20 Fırsat", "Tüm Betafix fiksasyon bantlarında toplu taleplere özel avantajlı oranlar tanımlandı.", 2, "firsat")
        ]
        cursor.executemany("INSERT INTO notifications (title, message, target_product_id, notif_type) VALUES (?, ?, ?, ?)", notifs)

    conn.commit()
    try:
        init_export_db(conn)
    except Exception as e:
        print(f"Warning: Could not initialize export db: {e}")
    conn.close()

try:
    init_db()
except Exception as e:
    print(f"Initial DB check warning: {e}")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# ==================== HTML BASE LAYOUT ====================
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Betasan Yönetim Paneli</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</head>
<body class="bg-slate-50 text-slate-900 min-h-screen flex flex-col">
    <!-- Üst Bar -->
    <header class="bg-[#0B3B60] text-white shadow-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 bg-white text-[#0B3B60] rounded-xl flex items-center justify-center font-extrabold text-xl shadow-inner">B</div>
                <div>
                    <span class="font-black tracking-wider text-lg">BETASAN</span>
                    <span class="text-xs bg-sky-800 text-sky-200 px-2 py-0.5 rounded-full ml-2 font-medium">Yönetim Paneli</span>
                </div>
            </div>
            <div class="flex items-center space-x-5 text-sm font-medium">
                <a href="{{ url_for('admin_dashboard') }}" class="hover:text-sky-300 transition flex items-center space-x-1"><i class="fa-solid fa-chart-pie"></i><span>Özet</span></a>
                <a href="{{ url_for('export_manager.admin_exports') }}" class="hover:text-sky-200 transition flex items-center space-x-1.5 bg-sky-900/70 text-sky-200 font-bold px-3 py-1.5 rounded-xl border border-sky-600/50 shadow-xs"><i class="fa-solid fa-ship text-sky-300"></i><span>İhracat Takip</span></a>
                <a href="{{ url_for('export_manager.admin_export_alerts') }}" class="hover:text-amber-200 transition flex items-center space-x-1.5 text-amber-300 font-bold"><i class="fa-solid fa-triangle-exclamation"></i><span>Alarmlar</span></a>
                <a href="{{ url_for('admin_products') }}" class="hover:text-sky-300 transition flex items-center space-x-1"><i class="fa-solid fa-box-archive"></i><span>Ürünler</span></a>
                <a href="{{ url_for('admin_categories') }}" class="hover:text-sky-300 transition flex items-center space-x-1"><i class="fa-solid fa-tags"></i><span>Kategoriler</span></a>
                <a href="{{ url_for('admin_inquiries') }}" class="hover:text-sky-300 transition flex items-center space-x-1"><i class="fa-solid fa-envelope-open-text"></i><span>Gelen Talepler</span></a>
                <a href="{{ url_for('admin_notifications') }}" class="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"><i class="fa-solid fa-bullhorn"></i><span>Bildirim Gönder</span></a>
            </div>
        </div>
    </header>

    <!-- Bilgi Şeridi -->
    <div class="bg-sky-100 border-b border-sky-200 py-2 text-xs text-sky-900">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
            <div class="flex items-center space-x-2">
                <i class="fa-solid fa-mobile-screen-button text-sky-600"></i>
                <span><strong>Mobil Uygulama API Adresi:</strong> <code class="bg-white px-2 py-0.5 rounded border border-sky-300 font-mono text-sky-800">http://{{ local_ip }}:5000/api/</code></span>
            </div>
            <span class="text-slate-500 hidden sm:inline">Telefonunuz ve bu bilgisayar aynı Wi-Fi ağına bağlıyken uygulama canlı verileri buradan çeker.</span>
        </div>
    </div>

    <!-- İçerik Alanı -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {% block content %}{% endblock %}
    </main>

    <footer class="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        Betasan Tıbbi Bant San. ve Tic. A.Ş. &copy; 2026 - Mobil Ürün ve Bildirim Yönetim Sistemi
    </footer>
</body>
</html>
"""

# ==================== WEB VIEWS ====================

@app.route("/")
@app.route("/admin")
def admin_dashboard():
    conn = get_db()
    product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    category_count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    discount_count = conn.execute("SELECT COUNT(*) FROM products WHERE discount_rate > 0").fetchone()[0]
    inquiry_count = conn.execute("SELECT COUNT(*) FROM order_inquiries").fetchone()[0]
    notif_count = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
    latest_products = conn.execute("SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id ORDER BY p.id DESC LIMIT 5").fetchall()
    conn.close()

    content = """
    {% extends "base" %}
    {% block content %}
    <div class="space-y-8">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
                <h1 class="text-2xl font-bold text-slate-800">Yönetim Paneli Genel Bakış</h1>
                <p class="text-sm text-slate-500 mt-1">Mobil uygulamada görünen ürünleri, kategorileri, bildirimleri ve gelen teklif taleplerini buradan yönetebilirsiniz.</p>
            </div>
            <div class="flex items-center space-x-3">
                <a href="{{ url_for('admin_notifications') }}" class="inline-flex items-center space-x-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-4 py-2.5 rounded-xl shadow transition text-sm">
                    <i class="fa-solid fa-bullhorn"></i>
                    <span>Tüm Kullanıcılara Bildirim At</span>
                </a>
                <a href="{{ url_for('admin_product_add') }}" class="inline-flex items-center space-x-2 bg-[#0B3B60] hover:bg-sky-900 text-white font-semibold px-4 py-2.5 rounded-xl shadow transition text-sm">
                    <i class="fa-solid fa-plus"></i>
                    <span>Yeni Ürün Ekle</span>
                </a>
            </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
            <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center space-x-4">
                <div class="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-lg"><i class="fa-solid fa-boxes-stacked"></i></div>
                <div>
                    <div class="text-2xl font-bold text-slate-800">{{ product_count }}</div>
                    <div class="text-xs font-medium text-slate-500">Toplam Ürün</div>
                </div>
            </div>
            <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center space-x-4">
                <div class="w-11 h-11 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center text-lg"><i class="fa-solid fa-layer-group"></i></div>
                <div>
                    <div class="text-2xl font-bold text-slate-800">{{ category_count }}</div>
                    <div class="text-xs font-medium text-slate-500">Kategori</div>
                </div>
            </div>
            <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center space-x-4">
                <div class="w-11 h-11 rounded-xl bg-red-50 text-red-600 flex items-center justify-center text-lg"><i class="fa-solid fa-fire"></i></div>
                <div>
                    <div class="text-2xl font-bold text-slate-800">{{ discount_count }}</div>
                    <div class="text-xs font-medium text-slate-500">İndirimli Ürün</div>
                </div>
            </div>
            <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center space-x-4">
                <div class="w-11 h-11 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center text-lg"><i class="fa-solid fa-bullhorn"></i></div>
                <div>
                    <div class="text-2xl font-bold text-slate-800">{{ notif_count }}</div>
                    <div class="text-xs font-medium text-slate-500">Gönderilen Bildirim</div>
                </div>
            </div>
            <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center space-x-4">
                <div class="w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg"><i class="fa-solid fa-receipt"></i></div>
                <div>
                    <div class="text-2xl font-bold text-slate-800">{{ inquiry_count }}</div>
                    <div class="text-xs font-medium text-slate-500">Gelen Sepet Talebi</div>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="p-6 border-b border-slate-100 flex items-center justify-between">
                <h2 class="text-lg font-bold text-slate-800">Son Eklenen Ürünler</h2>
                <a href="{{ url_for('admin_products') }}" class="text-sm font-semibold text-[#0B3B60] hover:text-sky-600">Tüm Ürünleri Gör &rarr;</a>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-slate-600">
                    <thead class="bg-slate-50 text-xs uppercase text-slate-400 font-semibold">
                        <tr>
                            <th class="px-6 py-3">Ürün</th>
                            <th class="px-6 py-3">Kod</th>
                            <th class="px-6 py-3">Kategori</th>
                            <th class="px-6 py-3">İndirim</th>
                            <th class="px-6 py-3 text-right">İşlem</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        {% for p in latest_products %}
                        <tr class="hover:bg-slate-50/50">
                            <td class="px-6 py-4 flex items-center space-x-3">
                                {% if p.image %}
                                    <img src="/uploads/{{ p.image }}" class="w-10 h-10 object-cover rounded-lg border border-slate-200">
                                {% else %}
                                    <div class="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center text-slate-400"><i class="fa-solid fa-image"></i></div>
                                {% endif %}
                                <span class="font-semibold text-slate-800">{{ p.name }}</span>
                            </td>
                            <td class="px-6 py-4 font-mono text-xs">{{ p.code or '-' }}</td>
                            <td class="px-6 py-4">{{ p.category_name or '-' }}</td>
                            <td class="px-6 py-4">
                                {% if p.discount_rate > 0 %}
                                    <span class="bg-red-50 text-red-600 font-bold px-2 py-0.5 rounded-full text-xs">%{{ p.discount_rate }} İndirim</span>
                                {% else %}
                                    <span class="text-slate-400">-</span>
                                {% endif %}
                            </td>
                            <td class="px-6 py-4 text-right space-x-2">
                                <a href="{{ url_for('admin_product_edit', id=p.id) }}" class="text-slate-600 hover:text-blue-600 font-medium text-xs"><i class="fa-solid fa-pen-to-square"></i> Düzenle</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_LAYOUT.replace("{% block content %}{% endblock %}", content),
                                  title="Genel Bakış",
                                  local_ip=get_local_ip(),
                                  product_count=product_count,
                                  category_count=category_count,
                                  discount_count=discount_count,
                                  inquiry_count=inquiry_count,
                                  notif_count=notif_count,
                                  latest_products=latest_products)

@app.route("/admin/products")
def admin_products():
    conn = get_db()
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category_id", "")
    query = """
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (p.name LIKE ? OR p.code LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    query += " ORDER BY p.id DESC"
    products = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY sort_order ASC").fetchall()
    conn.close()

    content = """
    {% extends "base" %}
    {% block content %}
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
                <h1 class="text-2xl font-bold text-slate-800">Ürün Yönetimi</h1>
                <p class="text-sm text-slate-500 mt-1">Tüm katalog ürünlerini görüntüleyin, yenilerini ekleyin veya düzenleyin.</p>
            </div>
            <a href="{{ url_for('admin_product_add') }}" class="inline-flex items-center space-x-2 bg-[#0B3B60] hover:bg-sky-900 text-white font-semibold px-4 py-2.5 rounded-xl shadow transition text-sm">
                <i class="fa-solid fa-plus"></i>
                <span>Yeni Ürün Ekle</span>
            </a>
        </div>

        <form method="GET" class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3">
            <div class="relative flex-1">
                <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-3 text-slate-400"></i>
                <input type="text" name="search" value="{{ request.args.get('search', '') }}" placeholder="Ürün adı veya kodu ile ara..." class="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
            </div>
            <select name="category_id" class="px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                <option value="">Tüm Kategoriler</option>
                {% for c in categories %}
                    <option value="{{ c.id }}" {% if request.args.get('category_id') == c.id|string %}selected{% endif %}>{{ c.name }}</option>
                {% endfor %}
            </select>
            <button type="submit" class="bg-slate-800 text-white px-5 py-2 rounded-xl text-sm font-semibold hover:bg-slate-700 transition">Filtrele</button>
        </form>

        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-slate-600">
                    <thead class="bg-slate-50 text-xs uppercase text-slate-400 font-semibold">
                        <tr>
                            <th class="px-6 py-3.5">Görsel</th>
                            <th class="px-6 py-3.5">Ürün Adı</th>
                            <th class="px-6 py-3.5">Kod</th>
                            <th class="px-6 py-3.5">Kategori</th>
                            <th class="px-6 py-3.5">İndirim</th>
                            <th class="px-6 py-3.5">Öne Çıkan</th>
                            <th class="px-6 py-3.5 text-right">İşlemler</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        {% for p in products %}
                        <tr class="hover:bg-slate-50/50">
                            <td class="px-6 py-4">
                                {% if p.image %}
                                    <img src="/uploads/{{ p.image }}" class="w-12 h-12 object-cover rounded-xl border border-slate-200 shadow-sm">
                                {% else %}
                                    <div class="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center text-slate-400 text-base"><i class="fa-solid fa-image"></i></div>
                                {% endif %}
                            </td>
                            <td class="px-6 py-4 font-bold text-slate-800 max-w-xs">{{ p.name }}</td>
                            <td class="px-6 py-4 font-mono text-xs font-semibold text-slate-600">{{ p.code or '-' }}</td>
                            <td class="px-6 py-4"><span class="bg-slate-100 text-slate-700 text-xs font-medium px-2.5 py-1 rounded-md">{{ p.category_name or 'Genel' }}</span></td>
                            <td class="px-6 py-4">
                                {% if p.discount_rate > 0 %}
                                    <span class="bg-red-50 text-red-600 font-bold px-2 py-0.5 rounded-full text-xs">%{{ p.discount_rate }}</span>
                                {% else %}
                                    <span class="text-slate-400 text-xs">Yok</span>
                                {% endif %}
                            </td>
                            <td class="px-6 py-4">
                                {% if p.is_featured %}
                                    <span class="text-amber-500 text-sm"><i class="fa-solid fa-star"></i></span>
                                {% else %}
                                    <span class="text-slate-300 text-sm"><i class="fa-regular fa-star"></i></span>
                                {% endif %}
                            </td>
                            <td class="px-6 py-4 text-right space-x-3">
                                <a href="{{ url_for('admin_product_edit', id=p.id) }}" class="text-blue-600 hover:text-blue-800 font-semibold text-xs"><i class="fa-solid fa-pen"></i> Düzenle</a>
                                <a href="{{ url_for('admin_product_delete', id=p.id) }}" onclick="return confirm('Bu ürünü silmek istediğinize emin misiniz?')" class="text-red-600 hover:text-red-800 font-semibold text-xs"><i class="fa-solid fa-trash"></i> Sil</a>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="7" class="px-6 py-12 text-center text-slate-400">Ürün bulunamadı.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_LAYOUT.replace("{% block content %}{% endblock %}", content),
                                  title="Ürünler",
                                  local_ip=get_local_ip(),
                                  products=products,
                                  categories=categories)

@app.route("/admin/products/add", methods=["GET", "POST"])
def admin_product_add():
    conn = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        category_id = request.form.get("category_id") or None
        description = request.form.get("description", "").strip()
        discount_rate = int(request.form.get("discount_rate") or 0)
        is_featured = 1 if request.form.get("is_featured") else 0
        is_active = 1 if request.form.get("is_active") else 0

        image_filename = None
        if "image" in request.files:
            file = request.files["image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(f"product_{int(datetime.now().timestamp())}_{file.filename}")
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_filename = filename

        conn.execute("""
            INSERT INTO products (name, code, category_id, description, image, discount_rate, is_featured, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, code, category_id, description, image_filename, discount_rate, is_featured, is_active))
        conn.commit()
        conn.close()
        return redirect(url_for("admin_products"))

    categories = conn.execute("SELECT * FROM categories ORDER BY sort_order ASC").fetchall()
    conn.close()

    content = """
    {% extends "base" %}
    {% block content %}
    <div class="max-w-3xl mx-auto space-y-6">
        <div class="flex items-center space-x-3">
            <a href="{{ url_for('admin_products') }}" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-arrow-left"></i></a>
            <h1 class="text-2xl font-bold text-slate-800">Yeni Ürün Ekle</h1>
        </div>

        <form method="POST" enctype="multipart/form-data" class="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div class="sm:col-span-2">
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Ürün Adı *</label>
                    <input type="text" name="name" required placeholder="Örn: Betaban İpek Tıbbi Flaster 5m x 5cm" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                </div>

                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Ürün Kodu</label>
                    <input type="text" name="code" placeholder="Örn: BT-102" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                </div>

                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Kategori</label>
                    <select name="category_id" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                        {% for c in categories %}
                            <option value="{{ c.id }}">{{ c.name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">İndirim Oranı (%)</label>
                    <input type="number" name="discount_rate" min="0" max="100" value="0" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                </div>

                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Ürün Görseli Yükle</label>
                    <input type="file" name="image" accept="image/*" class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl">
                </div>

                <div class="sm:col-span-2">
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Açıklama & Özellikler</label>
                    <textarea name="description" rows="4" placeholder="Ürünün yapısı, kullanım alanları..." class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]"></textarea>
                </div>

                <div class="sm:col-span-2 flex items-center space-x-6 pt-2">
                    <label class="flex items-center space-x-2 text-sm font-medium text-slate-700 cursor-pointer">
                        <input type="checkbox" name="is_featured" value="1" checked class="w-4 h-4 text-[#0B3B60] rounded border-slate-300">
                        <span>Öne Çıkan Ürün</span>
                    </label>
                    <label class="flex items-center space-x-2 text-sm font-medium text-slate-700 cursor-pointer">
                        <input type="checkbox" name="is_active" value="1" checked class="w-4 h-4 text-[#0B3B60] rounded border-slate-300">
                        <span>Aktif</span>
                    </label>
                </div>
            </div>

            <div class="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
                <a href="{{ url_for('admin_products') }}" class="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100 transition">İptal</a>
                <button type="submit" class="px-6 py-2.5 bg-[#0B3B60] hover:bg-sky-900 text-white font-semibold rounded-xl text-sm shadow transition">Ürünü Kaydet & Yayınla</button>
            </div>
        </form>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_LAYOUT.replace("{% block content %}{% endblock %}", content),
                                  title="Yeni Ürün Ekle",
                                  local_ip=get_local_ip(),
                                  categories=categories)

@app.route("/admin/products/edit/<int:id>", methods=["GET", "POST"])
def admin_product_edit(id):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()
    if not product:
        conn.close()
        return redirect(url_for("admin_products"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        category_id = request.form.get("category_id") or None
        description = request.form.get("description", "").strip()
        discount_rate = int(request.form.get("discount_rate") or 0)
        is_featured = 1 if request.form.get("is_featured") else 0
        is_active = 1 if request.form.get("is_active") else 0

        image_filename = product["image"]
        if "image" in request.files:
            file = request.files["image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(f"product_{int(datetime.now().timestamp())}_{file.filename}")
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_filename = filename

        conn.execute("""
            UPDATE products 
            SET name = ?, code = ?, category_id = ?, description = ?, image = ?, discount_rate = ?, is_featured = ?, is_active = ?
            WHERE id = ?
        """, (name, code, category_id, description, image_filename, discount_rate, is_featured, is_active, id))
        conn.commit()
        conn.close()
        return redirect(url_for("admin_products"))

    categories = conn.execute("SELECT * FROM categories ORDER BY sort_order ASC").fetchall()
    conn.close()

    content = """
    {% extends "base" %}
    {% block content %}
    <div class="max-w-3xl mx-auto space-y-6">
        <div class="flex items-center space-x-3">
            <a href="{{ url_for('admin_products') }}" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-arrow-left"></i></a>
            <h1 class="text-2xl font-bold text-slate-800">Ürünü Düzenle: {{ product.name }}</h1>
        </div>

        <form method="POST" enctype="multipart/form-data" class="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div class="sm:col-span-2">
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Ürün Adı *</label>
                    <input type="text" name="name" value="{{ product.name }}" required class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                </div>

                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Ürün Kodu</label>
                    <input type="text" name="code" value="{{ product.code or '' }}" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                </div>

                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Kategori</label>
                    <select name="category_id" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                        {% for c in categories %}
                            <option value="{{ c.id }}" {% if product.category_id == c.id %}selected{% endif %}>{{ c.name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">İndirim Oranı (%)</label>
                    <input type="number" name="discount_rate" min="0" max="100" value="{{ product.discount_rate }}" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                </div>

                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Görseli Değiştir</label>
                    <input type="file" name="image" accept="image/*" class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl">
                </div>

                <div class="sm:col-span-2">
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Açıklama & Özellikler</label>
                    <textarea name="description" rows="4" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">{{ product.description or '' }}</textarea>
                </div>

                <div class="sm:col-span-2 flex items-center space-x-6 pt-2">
                    <label class="flex items-center space-x-2 text-sm font-medium text-slate-700 cursor-pointer">
                        <input type="checkbox" name="is_featured" value="1" {% if product.is_featured %}checked{% endif %} class="w-4 h-4 text-[#0B3B60] rounded border-slate-300">
                        <span>Öne Çıkan Ürün</span>
                    </label>
                    <label class="flex items-center space-x-2 text-sm font-medium text-slate-700 cursor-pointer">
                        <input type="checkbox" name="is_active" value="1" {% if product.is_active %}checked{% endif %} class="w-4 h-4 text-[#0B3B60] rounded border-slate-300">
                        <span>Aktif</span>
                    </label>
                </div>
            </div>

            <div class="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
                <a href="{{ url_for('admin_products') }}" class="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100 transition">İptal</a>
                <button type="submit" class="px-6 py-2.5 bg-[#0B3B60] hover:bg-sky-900 text-white font-semibold rounded-xl text-sm shadow transition">Değişiklikleri Kaydet</button>
            </div>
        </form>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_LAYOUT.replace("{% block content %}{% endblock %}", content),
                                  title="Ürün Düzenle",
                                  local_ip=get_local_ip(),
                                  product=product,
                                  categories=categories)

@app.route("/admin/products/delete/<int:id>")
def admin_product_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_products"))

@app.route("/admin/categories", methods=["GET", "POST"])
def admin_categories():
    conn = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            slug = name.lower().replace(" ", "-").replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
            conn.execute("INSERT INTO categories (name, slug) VALUES (?, ?)", (name, slug))
            conn.commit()
        return redirect(url_for("admin_categories"))

    categories = conn.execute("SELECT c.*, COUNT(p.id) as product_count FROM categories c LEFT JOIN products p ON c.id = p.category_id GROUP BY c.id ORDER BY c.sort_order ASC, c.name ASC").fetchall()
    conn.close()

    content = """
    {% extends "base" %}
    {% block content %}
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div>
            <h2 class="text-xl font-bold text-slate-800 mb-4">Yeni Kategori Ekle</h2>
            <form method="POST" class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Kategori Adı</label>
                    <input type="text" name="name" required placeholder="Örn: Cerrahi Bantlar" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                </div>
                <button type="submit" class="w-full py-2.5 bg-[#0B3B60] text-white font-semibold rounded-xl text-sm hover:bg-sky-900 transition">Kategoriyi Ekle</button>
            </form>
        </div>

        <div class="lg:col-span-2">
            <h2 class="text-xl font-bold text-slate-800 mb-4">Mevcut Kategoriler</h2>
            <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <table class="w-full text-left text-sm text-slate-600">
                    <thead class="bg-slate-50 text-xs uppercase text-slate-400 font-semibold">
                        <tr>
                            <th class="px-6 py-3.5">Kategori Adı</th>
                            <th class="px-6 py-3.5">Ürün Sayısı</th>
                            <th class="px-6 py-3.5 text-right">İşlem</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        {% for c in categories %}
                        <tr class="hover:bg-slate-50/50">
                            <td class="px-6 py-4 font-bold text-slate-800">{{ c.name }}</td>
                            <td class="px-6 py-4"><span class="bg-sky-50 text-sky-700 font-bold px-2.5 py-1 rounded-full text-xs">{{ c.product_count }} Ürün</span></td>
                            <td class="px-6 py-4 text-right">
                                <a href="{{ url_for('admin_category_delete', id=c.id) }}" onclick="return confirm('Bu kategoriyi silmek istediğinize emin misiniz?')" class="text-red-500 hover:text-red-700 font-semibold text-xs"><i class="fa-solid fa-trash"></i> Sil</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_LAYOUT.replace("{% block content %}{% endblock %}", content),
                                  title="Kategoriler",
                                  local_ip=get_local_ip(),
                                  categories=categories)

@app.route("/admin/categories/delete/<int:id>")
def admin_category_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM categories WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_categories"))

@app.route("/admin/inquiries")
def admin_inquiries():
    conn = get_db()
    inquiries = conn.execute("SELECT * FROM order_inquiries ORDER BY id DESC").fetchall()
    conn.close()

    content = """
    {% extends "base" %}
    {% block content %}
    <div class="space-y-6">
        <div>
            <h1 class="text-2xl font-bold text-slate-800">Gelen Sepet & Teklif Talepleri</h1>
            <p class="text-sm text-slate-500 mt-1">Mobil uygulamadan müşterilerin WhatsApp veya E-Posta ile ilettiği sepet listeleri.</p>
        </div>

        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <table class="w-full text-left text-sm text-slate-600">
                <thead class="bg-slate-50 text-xs uppercase text-slate-400 font-semibold">
                    <tr>
                        <th class="px-6 py-3.5">Tarih</th>
                        <th class="px-6 py-3.5">Müşteri / Kurum</th>
                        <th class="px-6 py-3.5">İletişim</th>
                        <th class="px-6 py-3.5">Talep Edilen Ürünler</th>
                        <th class="px-6 py-3.5">Kanal</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    {% for inq in inquiries %}
                    <tr class="hover:bg-slate-50/50">
                        <td class="px-6 py-4 text-xs font-mono">{{ inq.created_at }}</td>
                        <td class="px-6 py-4 font-bold text-slate-800">{{ inq.customer_name or 'İsimsiz Müşteri' }}</td>
                        <td class="px-6 py-4 font-mono text-xs">{{ inq.customer_phone or '-' }}</td>
                        <td class="px-6 py-4 text-xs max-w-md whitespace-pre-wrap font-mono bg-slate-50 rounded p-2">{{ inq.items_json }}</td>
                        <td class="px-6 py-4"><span class="bg-emerald-50 text-emerald-700 text-xs font-bold px-2.5 py-1 rounded-full uppercase">{{ inq.channel }}</span></td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="5" class="px-6 py-12 text-center text-slate-400">Henüz iletilen bir sepet talebi bulunmuyor.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_LAYOUT.replace("{% block content %}{% endblock %}", content),
                                  title="Gelen Sepet Talepleri",
                                  local_ip=get_local_ip(),
                                  inquiries=inquiries)

# ==================== ENHANCED BROADCAST NOTIFICATION SYSTEM ====================

@app.route("/admin/notifications", methods=["GET", "POST"])
def admin_notifications():
    conn = get_db()
    sent_success = False

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()
        product_id = request.form.get("product_id") or None
        notif_type = request.form.get("notif_type") or "kampanya"

        if title and message:
            conn.execute("""
                INSERT INTO notifications (title, message, target_product_id, notif_type)
                VALUES (?, ?, ?, ?)
            """, (title, message, product_id, notif_type))
            conn.commit()
            sent_success = True

    notifications = conn.execute("""
        SELECT n.*, p.name as product_name 
        FROM notifications n 
        LEFT JOIN products p ON n.target_product_id = p.id 
        ORDER BY n.id DESC
    """).fetchall()

    products = conn.execute("SELECT id, name FROM products WHERE is_active = 1 ORDER BY name ASC").fetchall()
    registered_devices = conn.execute("SELECT COUNT(*) FROM device_tokens").fetchone()[0]
    conn.close()

    content = """
    {% extends "base" %}
    {% block content %}
    <div class="space-y-8">
        <!-- Başlık -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
                <div class="inline-flex items-center space-x-2 bg-amber-100 text-amber-900 text-xs font-bold px-3 py-1 rounded-full mb-2">
                    <i class="fa-solid fa-tower-broadcast animate-pulse text-amber-600"></i>
                    <span>Canlı Bildirim & Haber Yayın Merkezi</span>
                </div>
                <h1 class="text-2xl font-black text-slate-800">Tüm Kullanıcılara Anlık Bildirim Gönder</h1>
                <p class="text-sm text-slate-500 mt-1">Uygulamayı yüklemiş olan tüm müşterilerin telefon kilit ekranlarına ve durum çubuğuna anında bildirim gönderin.</p>
            </div>
            <div class="bg-white px-5 py-3 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-3">
                <div class="w-3 h-3 rounded-full bg-emerald-500 animate-ping"></div>
                <div>
                    <div class="text-xs text-slate-400 font-bold uppercase">Hedef Kitle</div>
                    <div class="text-sm font-extrabold text-slate-800">Tüm Aktif Kullanıcılar</div>
                </div>
            </div>
        </div>

        {% if sent_success %}
        <div class="bg-emerald-50 border-2 border-emerald-300 rounded-2xl p-4 flex items-center space-x-3 text-emerald-900">
            <div class="w-10 h-10 bg-emerald-500 text-white rounded-xl flex items-center justify-center text-lg shadow-sm"><i class="fa-solid fa-check"></i></div>
            <div>
                <h4 class="font-bold text-sm">Bildirim Başarıyla Gönderildi!</h4>
                <p class="text-xs text-emerald-700">Mesajınız veritabanına işlendi ve uygulamayı kullanan tüm cihazların ekranına iletildi.</p>
            </div>
        </div>
        {% endif %}

        <!-- Form ve Canlı Telefon Önizlemesi Izgarası -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <!-- Bildirim Gönderme Formu (Sol) -->
            <div class="lg:col-span-7 bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
                <h2 class="text-lg font-bold text-slate-800 flex items-center space-x-2">
                    <i class="fa-solid fa-pen-nib text-[#0B3B60]"></i>
                    <span>Yeni Bildirim Oluştur</span>
                </h2>

                <form method="POST" class="space-y-5">
                    <div>
                        <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Bildirim Başlığı *</label>
                        <input type="text" id="inputTitle" name="title" required 
                               placeholder="Örn: 🔥 Flaş İndirim: Tüm Flasterlerde %20 Fırsat!" 
                               oninput="updatePreview()"
                               class="w-full px-4 py-3 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60] font-medium">
                        <span class="text-[11px] text-slate-400">Kullanıcının dikkatini çekecek kısa ve net bir başlık yazın.</span>
                    </div>

                    <div>
                        <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Duyuru / Kampanya Mesajı *</label>
                        <textarea id="inputMessage" name="message" required rows="3" 
                                  placeholder="Örn: Hastanelere ve kliniklere özel toplu alımlarda geçerli indirimlerimiz başladı. İncelemek için hemen dokunun!" 
                                  oninput="updatePreview()"
                                  class="w-full px-4 py-3 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60] font-medium"></textarea>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Bildirim Tipi</label>
                            <select name="notif_type" class="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                                <option value="kampanya">🔥 Kampanya & İndirim</option>
                                <option value="haber">📢 Kurumsal Haber / Duyuru</option>
                                <option value="yeni_urun">📦 Yeni Ürün Tanıtımı</option>
                                <option value="acil">⚡ Önemli Bilgilendirme</option>
                            </select>
                        </div>

                        <div>
                            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">İlgili Ürün (Dokununca Açılsın)</label>
                            <select id="selectProduct" name="product_id" onchange="updatePreview()" class="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0B3B60]">
                                <option value="">Genel Duyuru (Ürün Yok)</option>
                                {% for p in products %}
                                    <option value="{{ p.id }}">{{ p.name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>

                    <div class="pt-4 border-t border-slate-100">
                        <button type="submit" class="w-full py-3.5 bg-gradient-to-r from-[#0B3B60] to-sky-700 hover:from-sky-900 hover:to-sky-800 text-white font-bold rounded-xl text-base shadow-lg transition flex items-center justify-center space-x-2">
                            <i class="fa-solid fa-paper-plane text-sky-200"></i>
                            <span>Tüm Kullanıcıların Telefonlarına Gönder</span>
                        </button>
                        <p class="text-center text-xs text-slate-400 mt-2">Bu işlem geri alınamaz; bildirim tüm bağlı telefonların ekranına anında yansır.</p>
                    </div>
                </form>
            </div>

            <!-- Canlı Telefon Önizlemesi (Sağ) -->
            <div class="lg:col-span-5 flex flex-col items-center">
                <div class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
                    <i class="fa-solid fa-mobile-screen"></i>
                    <span>Kullanıcının Telefonundaki Canlı Önizleme</span>
                </div>

                <!-- Telefon Mockup -->
                <div class="w-72 bg-slate-900 rounded-[42px] p-3 shadow-2xl border-4 border-slate-800">
                    <div class="w-full h-112 bg-slate-950 rounded-[34px] p-4 text-white flex flex-col justify-between overflow-hidden relative" style="min-height: 480px;">
                        <!-- Ekran Üst Durum Çubuğu -->
                        <div class="flex justify-between items-center text-[10px] text-slate-400 px-1 pt-1">
                            <span>09:45</span>
                            <div class="flex items-center space-x-1">
                                <i class="fa-solid fa-wifi"></i>
                                <i class="fa-solid fa-signal"></i>
                                <i class="fa-solid fa-battery-full"></i>
                            </div>
                        </div>

                        <!-- Kilit Ekranı / Durum Bildirim Kartı -->
                        <div class="my-auto space-y-3">
                            <div class="text-center text-xs text-slate-400 font-medium">Kilit Ekranı Bildirimi</div>

                            <div class="bg-white/95 text-slate-900 rounded-2xl p-3.5 shadow-lg backdrop-blur border border-white/20 transition-all duration-300">
                                <div class="flex items-center justify-between mb-1.5">
                                    <div class="flex items-center space-x-2">
                                        <div class="w-5 h-5 bg-[#0B3B60] text-white rounded-md flex items-center justify-center text-[10px] font-black">B</div>
                                        <span class="text-xs font-extrabold text-[#0B3B60]">BETASAN</span>
                                    </div>
                                    <span class="text-[10px] text-slate-400">Şimdi</span>
                                </div>

                                <div id="previewTitle" class="text-xs font-bold text-slate-900 line-clamp-1">
                                    Örnek Kampanya Başlığı
                                </div>
                                <div id="previewBody" class="text-[11px] text-slate-600 mt-0.5 line-clamp-2 leading-relaxed">
                                    Bildirim mesajınızı yazdıkça telefon ekranında nasıl görüneceği burada canlı güncellenir.
                                </div>

                                <div id="previewAction" class="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-sky-700 font-bold">
                                    <span>Dokununca İncele</span>
                                    <i class="fa-solid fa-chevron-right text-[8px]"></i>
                                </div>
                            </div>
                        </div>

                        <!-- Alt Kilit İkonu -->
                        <div class="text-center pb-2">
                            <div class="w-8 h-1 bg-white/40 rounded-full mx-auto"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Gönderilen Bildirimlerin Listesi -->
        <div class="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden mt-8">
            <div class="p-6 border-b border-slate-100 flex items-center justify-between">
                <div>
                    <h2 class="text-lg font-bold text-slate-800">Gönderilen Bildirim Geçmişi</h2>
                    <p class="text-xs text-slate-500 mt-0.5">Daha önce tüm kullanıcılara gönderilmiş olan duyurular.</p>
                </div>
                <span class="bg-slate-100 text-slate-700 text-xs font-bold px-3 py-1 rounded-full">{{ notifications|length }} Bildirim</span>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-slate-600">
                    <thead class="bg-slate-50 text-xs uppercase text-slate-400 font-semibold">
                        <tr>
                            <th class="px-6 py-3.5">Başlık & Mesaj</th>
                            <th class="px-6 py-3.5">Tip</th>
                            <th class="px-6 py-3.5">Bağlantılı Ürün</th>
                            <th class="px-6 py-3.5">Gönderim Tarihi</th>
                            <th class="px-6 py-3.5 text-right">İşlem</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        {% for n in notifications %}
                        <tr class="hover:bg-slate-50/50">
                            <td class="px-6 py-4 max-w-md">
                                <div class="font-bold text-slate-800 text-sm">{{ n.title }}</div>
                                <div class="text-xs text-slate-500 mt-0.5 line-clamp-2">{{ n.message }}</div>
                            </td>
                            <td class="px-6 py-4">
                                <span class="bg-sky-50 text-sky-700 text-xs font-bold px-2.5 py-1 rounded-full uppercase">{{ n.notif_type or 'Duyuru' }}</span>
                            </td>
                            <td class="px-6 py-4">
                                {% if n.product_name %}
                                    <span class="text-xs font-semibold text-[#0B3B60] flex items-center space-x-1">
                                        <i class="fa-solid fa-link text-[10px]"></i>
                                        <span>{{ n.product_name }}</span>
                                    </span>
                                {% else %}
                                    <span class="text-slate-400 text-xs">-</span>
                                {% endif %}
                            </td>
                            <td class="px-6 py-4 text-xs font-mono text-slate-400">{{ n.sent_at }}</td>
                            <td class="px-6 py-4 text-right">
                                <a href="{{ url_for('admin_notification_delete', id=n.id) }}" onclick="return confirm('Bu bildirimi silmek istediğinize emin misiniz?')" class="text-red-500 hover:text-red-700 font-semibold text-xs"><i class="fa-solid fa-trash"></i> Sil</a>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="5" class="px-6 py-12 text-center text-slate-400">Henüz gönderilmiş bir bildirim bulunmuyor.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function updatePreview() {
            var title = document.getElementById('inputTitle').value.trim();
            var message = document.getElementById('inputMessage').value.trim();
            var sel = document.getElementById('selectProduct');
            var prodText = sel.options[sel.selectedIndex].text;

            document.getElementById('previewTitle').innerText = title || "Örnek Kampanya Başlığı";
            document.getElementById('previewBody').innerText = message || "Bildirim mesajınızı yazdıkça telefon ekranında nasıl görüneceği burada canlı güncellenir.";

            var act = document.getElementById('previewAction');
            if (sel.value) {
                act.innerHTML = "<span>Ürünü Gör: " + prodText.substring(0, 20) + "...</span><i class='fa-solid fa-chevron-right text-[8px]'></i>";
            } else {
                act.innerHTML = "<span>Duyuruyu İncele</span><i class='fa-solid fa-chevron-right text-[8px]'></i>";
            }
        }
    </script>
    {% endblock %}
    """
    return render_template_string(BASE_LAYOUT.replace("{% block content %}{% endblock %}", content),
                                  title="Tüm Kullanıcılara Bildirim Gönder",
                                  local_ip=get_local_ip(),
                                  notifications=notifications,
                                  products=products,
                                  registered_devices=registered_devices,
                                  sent_success=sent_success)

@app.route("/admin/notifications/delete/<int:id>")
def admin_notification_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM notifications WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_notifications"))

@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ==================== MOBILE REST API ====================

def make_image_url(image_name):
    if not image_name:
        return None
    host = request.host
    return f"http://{host}/uploads/{image_name}"

@app.route("/api/get_products.php", methods=["GET"])
@app.route("/api/products", methods=["GET"])
def api_get_products():
    category_id = request.args.get("category_id")
    search = request.args.get("search", "").strip()
    only_discounted = request.args.get("only_discounted")

    conn = get_db()
    query = """
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.is_active = 1
    """
    params = []
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if search:
        query += " AND (p.name LIKE ? OR p.code LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if only_discounted in ("1", "true"):
        query += " AND p.discount_rate > 0"
    query += " ORDER BY p.id DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    data = []
    for r in rows:
        data.append({
            "id": r["id"],
            "name": r["name"],
            "code": r["code"],
            "category_id": r["category_id"],
            "category_name": r["category_name"],
            "description": r["description"],
            "image_url": make_image_url(r["image"]),
            "discount_rate": r["discount_rate"],
            "has_discount": r["discount_rate"] > 0,
            "is_featured": bool(r["is_featured"]),
            "created_at": str(r["created_at"])
        })
    return jsonify({"success": True, "data": data})

@app.route("/api/get_categories.php", methods=["GET"])
@app.route("/api/categories", methods=["GET"])
def api_get_categories():
    conn = get_db()
    rows = conn.execute("""
        SELECT c.*, COUNT(p.id) as product_count 
        FROM categories c 
        LEFT JOIN products p ON c.id = p.category_id AND p.is_active = 1
        GROUP BY c.id 
        ORDER BY c.sort_order ASC, c.name ASC
    """).fetchall()
    conn.close()
    data = []
    for r in rows:
        data.append({
            "id": r["id"],
            "name": r["name"],
            "slug": r["slug"],
            "icon": r["icon"],
            "product_count": r["product_count"]
        })
    return jsonify({"success": True, "data": data})

@app.route("/api/get_banners.php", methods=["GET"])
@app.route("/api/banners", methods=["GET"])
def api_get_banners():
    conn = get_db()
    rows = conn.execute("SELECT * FROM banners WHERE is_active = 1 ORDER BY id ASC").fetchall()
    conn.close()
    data = []
    for r in rows:
        data.append({
            "id": r["id"],
            "title": r["title"],
            "subtitle": r["subtitle"],
            "image_url": make_image_url(r["image"]),
            "badge": r["badge"],
            "product_id": r["product_id"]
        })
    return jsonify({"success": True, "data": data})

@app.route("/api/get_notifications.php", methods=["GET"])
@app.route("/api/notifications", methods=["GET"])
def api_get_notifications():
    conn = get_db()
    rows = conn.execute("""
        SELECT n.*, p.name as product_name, p.image as product_image
        FROM notifications n 
        LEFT JOIN products p ON n.target_product_id = p.id 
        ORDER BY n.id DESC
    """).fetchall()
    conn.close()
    data = []
    for r in rows:
        data.append({
            "id": r["id"],
            "title": r["title"],
            "message": r["message"],
            "target_product_id": r["target_product_id"],
            "product_name": r["product_name"],
            "product_image_url": make_image_url(r["product_image"]),
            "sent_at": str(r["sent_at"])
        })
    return jsonify({"success": True, "data": data})

@app.route("/api/get_product_detail.php", methods=["GET"])
def api_get_product_detail():
    pid = request.args.get("id")
    if not pid:
        return jsonify({"success": False, "message": "ID gerekli"}), 400
    conn = get_db()
    r = conn.execute("SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.id = ?", (pid,)).fetchone()
    conn.close()
    if not r:
        return jsonify({"success": False, "message": "Ürün bulunamadı"}), 404
    return jsonify({
        "success": True,
        "data": {
            "id": r["id"],
            "name": r["name"],
            "code": r["code"],
            "category_id": r["category_id"],
            "category_name": r["category_name"],
            "description": r["description"],
            "image_url": make_image_url(r["image"]),
            "discount_rate": r["discount_rate"],
            "has_discount": r["discount_rate"] > 0,
            "is_featured": bool(r["is_featured"]),
            "created_at": str(r["created_at"])
        }
    })

@app.route("/api/submit_inquiry.php", methods=["POST"])
def api_submit_inquiry():
    data = request.get_json(silent=True) or request.form
    customer_name = data.get("customer_name")
    customer_phone = data.get("customer_phone")
    items_json = str(data.get("items") or data.get("message") or "")
    note = data.get("note")
    channel = data.get("channel", "app")

    conn = get_db()
    conn.execute("""
        INSERT INTO order_inquiries (customer_name, customer_phone, items_json, note, channel)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_name, customer_phone, items_json, note, channel))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Teklif talebi başarıyla alındı"})

@app.route("/api/register_device.php", methods=["POST"])
def api_register_device():
    data = request.get_json(silent=True) or request.form
    token = data.get("token")
    device_type = data.get("device_type", "android")
    if token:
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO device_tokens (token, device_type) VALUES (?, ?)", (token, device_type))
        conn.commit()
        conn.close()
    return jsonify({"success": True, "message": "Cihaz başarıyla kaydedildi"})

# ==================== UPTIMEROBOT & MONITORING (ASLA UYUMAYAN SUNUCU & OTOMATİK DENETİM) ====================

@app.route("/ping")
@app.route("/health")
def ping():
    """
    UptimeRobot her 10 dakikada bir bu adresi yokladığında:
    1. Sunucunun uykuya (Cold Start) dalmasını engeller.
    2. İhracat takip kural motorunu tetikler; geciken evrak varsa push & Telegram atar!
    """
    conn = get_db()
    checked_count = 0
    try:
        from export_manager import run_export_rule_engine
        alerts = run_export_rule_engine(conn)
        checked_count = len(alerts)
    except Exception as e:
        print(f"Ping kural motoru uyarısı: {e}")
    finally:
        conn.close()

    return jsonify({
        "status": "online",
        "service": "Betasan Export Tracker",
        "timestamp": datetime.now().isoformat(),
        "alerts_triggered": checked_count,
        "message": "Sunucu aktif ve uyanık tutuluyor."
    })

if __name__ == "__main__":
    init_db()
    local_ip = get_local_ip()
    port = 5000
    print("=" * 65)
    print("  BETASAN MOBİL UYGULAMA ADMİN PANELİ & API SUNUCUSU")
    print("=" * 65)
    print(f"  * Web Yönetim Paneli:  http://localhost:{port}/admin")
    print(f"  * Bildirim Merkezi:    http://localhost:{port}/admin/notifications")
    print(f"  * Mobil API Adresi:    http://{local_ip}:{port}/api/")
    print("=" * 65)
    print("  Tarayıcı açılıyor...")
    try:
        webbrowser.open(f"http://localhost:{port}/admin/notifications")
    except Exception:
        pass
    app.run(host="0.0.0.0", port=port, debug=False)
