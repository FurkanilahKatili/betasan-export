-- Betasan İhracat Operasyon, Evrak Takip & Akıllı Bildirim Veritabanı Şeması
-- Karakter seti UTF-8 (Türkçe karakter tam destekli)

-- 1. İhracat Dosyaları Tablosu
CREATE TABLE IF NOT EXISTS `export_shipments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `file_no` VARCHAR(50) NOT NULL UNIQUE,
  `customer_name` VARCHAR(255) NOT NULL,
  `country` VARCHAR(100) NOT NULL,
  `destination_port` VARCHAR(150) DEFAULT NULL,
  `incoterm` VARCHAR(20) DEFAULT 'FOB',
  `transport_mode` VARCHAR(20) DEFAULT 'sea', -- 'sea', 'road', 'air'
  `carrier_forwarder` VARCHAR(200) DEFAULT NULL,
  `loading_date` DATE DEFAULT NULL,
  `cutoff_datetime` DATETIME DEFAULT NULL,
  `etd` DATE DEFAULT NULL,
  `eta` DATE DEFAULT NULL,
  `status` VARCHAR(30) DEFAULT 'preparing', -- 'preparing', 'customs', 'in_transit', 'delivered', 'completed'
  `notes` TEXT DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. İhracat Evrak & Görev Matrisi Tablosu
CREATE TABLE IF NOT EXISTS `export_tasks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `shipment_id` INT NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `category` VARCHAR(50) DEFAULT 'document', -- 'document', 'customs', 'transport', 'payment', 'courier'
  `is_completed` TINYINT(1) DEFAULT 0,
  `completed_at` VARCHAR(50) DEFAULT NULL,
  `due_datetime` VARCHAR(50) DEFAULT NULL,
  `document_file_url` VARCHAR(255) DEFAULT NULL,
  `tracking_code` VARCHAR(100) DEFAULT NULL,
  `notes` TEXT DEFAULT NULL,
  `priority` VARCHAR(20) DEFAULT 'normal', -- 'urgent', 'normal', 'low'
  FOREIGN KEY (`shipment_id`) REFERENCES `export_shipments`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Akıllı Bildirim & Kural Alarmları Tablosu
CREATE TABLE IF NOT EXISTS `export_alerts` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `shipment_id` INT NOT NULL,
  `task_id` INT DEFAULT NULL,
  `alert_type` VARCHAR(50) NOT NULL, -- 'cutoff_approaching', 'missing_doc', 'overdue_task', 'courier_missing'
  `severity` VARCHAR(20) DEFAULT 'warning', -- 'danger', 'warning', 'info'
  `title` VARCHAR(255) NOT NULL,
  `message` TEXT NOT NULL,
  `is_resolved` TINYINT(1) DEFAULT 0,
  `snooze_until` VARCHAR(50) DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`shipment_id`) REFERENCES `export_shipments`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`task_id`) REFERENCES `export_tasks`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. İhracat Ayarları (Telegram & Cron)
CREATE TABLE IF NOT EXISTS `export_settings` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `key` VARCHAR(100) NOT NULL UNIQUE,
  `value` TEXT DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- notifications tablosuna notif_type alanı (varsa hata vermez)
ALTER TABLE `notifications` ADD COLUMN IF NOT EXISTS `notif_type` VARCHAR(50) DEFAULT 'kampanya';

-- Başlangıç Ayarları
INSERT INTO `export_settings` (`key`, `value`) VALUES
('telegram_bot_token', ''),
('telegram_chat_id', ''),
('auto_push_fcm', '1'),
('daily_morning_summary', '1')
ON DUPLICATE KEY UPDATE `key`=`key`;

-- Demo Başlangıç Verileri
INSERT INTO `export_shipments` (`id`, `file_no`, `customer_name`, `country`, `destination_port`, `incoterm`, `transport_mode`, `carrier_forwarder`, `cutoff_datetime`, `etd`, `eta`, `status`, `notes`) VALUES
(1, 'EXP-2026-DE-001', 'MedTech Healthcare GmbH', 'Almanya', 'Hamburg Limanı', 'FOB', 'sea', 'Maersk Line / Kuehne+Nagel', DATE_ADD(NOW(), INTERVAL 28 HOUR), DATE_ADD(CURDATE(), INTERVAL 2 DAY), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'preparing', '2x40HC Tıbbi Flaster ve Elastik Bandaj sevkiyatı.'),
(2, 'EXP-2026-IT-002', 'Sanitaria Pharma Nord S.r.l.', 'İtalya', 'Milano Terminali', 'DAP', 'road', 'Ekol Lojistik (Tır)', NULL, SUBDATE(CURDATE(), 1), DATE_ADD(CURDATE(), INTERVAL 4 DAY), 'customs', 'Kapı teslimi medikal sarf malzemesi ihracatı.'),
(3, 'EXP-2026-EG-003', 'Cairo Medical Supply Co.', 'Mısır', 'İskenderiye Limanı', 'CIF', 'sea', 'MSC Mediterranean Shipping', NULL, SUBDATE(CURDATE(), 4), DATE_ADD(CURDATE(), INTERVAL 9 DAY), 'in_transit', 'Akreditifli satış (L/C). Orijinal evraklar müşteriye kargolanmalı.')
ON DUPLICATE KEY UPDATE `file_no`=`file_no`;

-- Demo Görevler (Almanya)
INSERT INTO `export_tasks` (`shipment_id`, `title`, `category`, `is_completed`, `due_datetime`, `notes`, `priority`) VALUES
(1, 'Ticari Fatura (Commercial Invoice)', 'document', 1, NULL, 'Fatura kesildi ve onaylandı.', 'urgent'),
(1, 'Çeki Listesi (Packing List)', 'document', 1, NULL, 'Depo koli adetleri doğrulandı.', 'urgent'),
(1, 'ATR Dolaşım Belgesi Düzenlenmesi', 'document', 0, DATE_ADD(NOW(), INTERVAL 20 HOUR), 'Gümrükçüye iletilecek.', 'normal'),
(1, 'Konşimento Talimatı (BL Draft Instruction)', 'transport', 0, DATE_ADD(NOW(), INTERVAL 12 HOUR), 'Acenteye acil iletilmeli! Cutoff yaklaşıyor.', 'urgent'),
(1, 'İhracat Gümrük Beyannamesi Tescili', 'customs', 0, DATE_ADD(NOW(), INTERVAL 28 HOUR), 'Gümrük müşavirinden teyit bekleniyor.', 'urgent'),
(1, 'Analiz & Kalite Sertifikası (COA / CE)', 'document', 1, NULL, 'Kalite kontrol raporu hazır.', 'normal'),
(1, 'Orijinal Evrak Kargosu (DHL/FedEx)', 'courier', 0, DATE_ADD(NOW(), INTERVAL 72 HOUR), 'Gemi kalktıktan sonra kargolanacak.', 'urgent');
