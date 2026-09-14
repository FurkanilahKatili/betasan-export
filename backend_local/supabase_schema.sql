-- ==============================================================================
-- BETASAN MEDİKAL - SUPABASE (POSTGRESQL) VERİTABANI ŞEMASI
-- Bu betiği Supabase SQL Editor'e yapıştırıp RUN butonuna basınız.
-- ==============================================================================

-- 1. KATEGORİLER TABLOSU
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT,
    icon TEXT,
    sort_order INTEGER DEFAULT 0
);

-- 2. ÜRÜNLER TABLOSU
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    description TEXT,
    image TEXT,
    discount_rate INTEGER DEFAULT 0,
    is_featured INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. BANNERLAR TABLOSU
CREATE TABLE IF NOT EXISTS banners (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    subtitle TEXT,
    image TEXT,
    badge TEXT,
    product_id INTEGER,
    is_active INTEGER DEFAULT 1
);

-- 4. BİLDİRİMLER TABLOSU
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    target_product_id INTEGER,
    notif_type TEXT DEFAULT 'ihracat',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. MOBİL CİHAZ TOKENLARI TABLOSU
CREATE TABLE IF NOT EXISTS device_tokens (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE,
    device_type TEXT DEFAULT 'android',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. TEKLİF & SİPARİŞ TALEPLERİ TABLOSU
CREATE TABLE IF NOT EXISTS order_inquiries (
    id SERIAL PRIMARY KEY,
    customer_name TEXT,
    customer_phone TEXT,
    items_json TEXT,
    note TEXT,
    channel TEXT DEFAULT 'whatsapp',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. İHRACAT SEVKİYATLARI TABLOSU
CREATE TABLE IF NOT EXISTS export_shipments (
    id SERIAL PRIMARY KEY,
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. İHRACAT GÖREV & EVRAK MATRİSİ TABLOSU
CREATE TABLE IF NOT EXISTS export_tasks (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER NOT NULL REFERENCES export_shipments(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    category TEXT DEFAULT 'document',
    is_completed INTEGER DEFAULT 0,
    completed_at TEXT,
    due_datetime TEXT,
    document_file_url TEXT,
    tracking_code TEXT,
    notes TEXT,
    priority TEXT DEFAULT 'normal'
);

-- 9. İHRACAT UYARI & ALARM MERKEZİ TABLOSU
CREATE TABLE IF NOT EXISTS export_alerts (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER NOT NULL REFERENCES export_shipments(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES export_tasks(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    severity TEXT DEFAULT 'warning',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_resolved INTEGER DEFAULT 0,
    snooze_until TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. İHRACAT SİSTEM AYARLARI TABLOSU
CREATE TABLE IF NOT EXISTS export_settings (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE,
    value TEXT
);

-- ==============================================================================
-- BAŞLANGIÇ VERİLERİ (SEED DATA)
-- ==============================================================================

-- Kategori Verileri
INSERT INTO categories (name, slug, icon, sort_order)
VALUES 
    ('Tıbbi Flasterler', 'tibbi-flasterler', 'bandage', 1),
    ('Fiksasyon Bantları', 'fiksasyon-bantlari', 'tape', 2),
    ('Enjeksiyon & Kan Alma', 'enjeksiyon-kan-alma', 'syringe', 3),
    ('Yara Bakım & Gazlı Bez', 'yara-bakim', 'cross', 4),
    ('İlk Yardım & Destek', 'ilk-yardim', 'heart-pulse', 5)
ON CONFLICT DO NOTHING;

-- Örnek Ürün Verileri
INSERT INTO products (name, code, category_id, description, image, discount_rate, is_featured, is_active)
VALUES
    ('Betaban İpek Tıbbi Flaster 5m x 5cm', 'BT-101', 1, 'Cilt dostu çinko oksit yapışkanı ve ipek dokusu ile hassas pansuman sabitlemeleri için idealdir.', NULL, 15, 1, 1),
    ('Betafix Elastik Tıbbi Fiksasyon Bandı 10m x 10cm', 'BF-205', 2, 'Hava geçirgen, esnek non-woven kumaş yapısıyla hareketli eklem bölgelerinde güvenli tutuş sağlar.', NULL, 20, 1, 1),
    ('Betaseri Yuvarlak Enjeksiyon Bandı (100''lü)', 'BS-310', 3, 'Aşı, kan alma ve enjeksiyon sonrası emici pedli hipoalerjenik yuvarlak bant.', NULL, 0, 1, 1),
    ('Betaplast PU Su Geçirmez Şeffaf Film Flaster 10m x 5cm', 'BP-404', 1, 'Su geçirmez ve bakteri bariyeri oluşturan poliüretan film.', NULL, 10, 1, 1),
    ('Betasorb Steril Gaz Kompres 7.5cm x 7.5cm (50''li)', 'BG-501', 4, 'Yüksek sıvı emiciliğine sahip %100 saf pamuk hidrofil gaz kompres.', NULL, 0, 0, 1)
ON CONFLICT DO NOTHING;

-- Sistem Ayarları
INSERT INTO export_settings (key, value)
VALUES 
    ('telegram_bot_token', ''),
    ('telegram_chat_id', ''),
    ('cutoff_alert_hours', '48'),
    ('auto_alert_enabled', '1'),
    ('company_title', 'Betasan Bant Sanayi ve Ticaret A.Ş.')
ON CONFLICT (key) DO NOTHING;

-- Örnek Canlı İhracat Sevkiyatı (Test için)
INSERT INTO export_shipments (file_no, customer_name, country, destination_port, incoterm, transport_mode, carrier_forwarder, loading_date, cutoff_datetime, etd, eta, status, notes)
VALUES (
    'EXP-2026-DE01',
    'Medizin Vertrieb GmbH',
    'Almanya',
    'Hamburg Port',
    'CIF',
    'sea',
    'Maersk Line',
    to_char(CURRENT_DATE + interval '2 days', 'YYYY-MM-DD'),
    to_char(CURRENT_TIMESTAMP + interval '36 hours', 'YYYY-MM-DDTHH24:MI'),
    to_char(CURRENT_DATE + interval '4 days', 'YYYY-MM-DD'),
    to_char(CURRENT_DATE + interval '12 days', 'YYYY-MM-DD'),
    'preparing',
    'Almanya medikal flaster sevkiyatı. ATR belgesi ve analiz sertifikası zorunludur.'
)
ON CONFLICT (file_no) DO NOTHING;

-- Örnek Sevkiyatın Görevleri
INSERT INTO export_tasks (shipment_id, title, category, is_completed, due_datetime, priority)
SELECT 
    s.id, 
    t.title, 
    t.category, 
    0, 
    s.cutoff_datetime, 
    t.priority
FROM export_shipments s
CROSS JOIN (
    VALUES 
        ('Commercial Invoice (İhracat Faturası)', 'document', 'high'),
        ('Packing List (Çeki Listesi)', 'document', 'high'),
        ('B/L Draft (Konşimento Taslağı Onayı)', 'document', 'high'),
        ('ATR / Menşe İspat Belgesi', 'document', 'high'),
        ('Analiz & Uygunluk Sertifikası', 'document', 'normal'),
        ('Orijinal Evrak Kurye Takibi', 'courier', 'normal')
) AS t(title, category, priority)
WHERE s.file_no = 'EXP-2026-DE01'
ON CONFLICT DO NOTHING;
