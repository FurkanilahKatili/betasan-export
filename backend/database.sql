-- Betasan Mobil Uygulama & Web Yönetim Paneli Veritabanı Şeması
-- Karakter seti UTF-8 (Türkçe karakter tam destekli)

CREATE TABLE IF NOT EXISTS `categories` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(150) NOT NULL,
  `slug` VARCHAR(150) DEFAULT NULL,
  `icon` VARCHAR(100) DEFAULT 'folder',
  `sort_order` INT DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `products` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `category_id` INT DEFAULT NULL,
  `name` VARCHAR(255) NOT NULL,
  `code` VARCHAR(100) DEFAULT NULL,
  `description` TEXT DEFAULT NULL,
  `image` VARCHAR(255) DEFAULT NULL,
  `discount_rate` INT DEFAULT 0,
  `is_featured` TINYINT(1) DEFAULT 0,
  `is_active` TINYINT(1) DEFAULT 1,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `notifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) NOT NULL,
  `message` TEXT NOT NULL,
  `image` VARCHAR(255) DEFAULT NULL,
  `target_product_id` INT DEFAULT NULL,
  `sent_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `device_tokens` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `token` TEXT NOT NULL,
  `device_type` VARCHAR(20) DEFAULT 'android',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `admins` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(100) NOT NULL UNIQUE,
  `password` VARCHAR(255) NOT NULL,
  `full_name` VARCHAR(150) DEFAULT 'Betasan Yöneticisi',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `order_inquiries` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `customer_name` VARCHAR(150) NOT NULL,
  `customer_phone` VARCHAR(50) DEFAULT NULL,
  `customer_notes` TEXT DEFAULT NULL,
  `channel` VARCHAR(20) DEFAULT 'whatsapp', -- 'whatsapp' veya 'email'
  `items_summary` TEXT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Başlangıç Kategorileri (Betasan Medikal Ürün Grupları)
INSERT INTO `categories` (`name`, `slug`, `icon`, `sort_order`) VALUES
('Tıbbi Flasterler', 'tibbi-flasterler', 'medical-tape', 1),
('Elastik Bandajlar', 'elastik-bandajlar', 'bandage', 2),
('Sargı Bezleri & Gaz Kompresler', 'sargi-bezleri', 'gauze', 3),
('Yara Bakım & İlk Yardım', 'yara-bakim', 'first-aid', 4),
('Cerrahi ve Tıbbi Sarf Malzemeleri', 'tibbi-sarf', 'box', 5)
ON DUPLICATE KEY UPDATE `name`=`name`;

-- Varsayılan Yönetici Girişi:
-- Kullanıcı Adı: admin
-- Şifre: betasan2026!
INSERT INTO `admins` (`username`, `password`, `full_name`) VALUES
('admin', '$2y$10$w095tYwS5F7V4rR6qGk4h.U5Z2N2xKj9y1vQo6.hQ1eTj9W0qL/eO', 'Betasan Admin')
ON DUPLICATE KEY UPDATE `username`=`username`;
