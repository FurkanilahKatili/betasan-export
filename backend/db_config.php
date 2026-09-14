<?php
/**
 * Betasan - Veritabanı ve Genel Yapılandırma Dosyası
 * cPanel üzerindeki MySQL bilgilerinizi buraya girebilirsiniz.
 */

// Hata raporlama (Canlıya aldığınızda 0 yapabilirsiniz)
error_reporting(E_ALL);
ini_set('display_errors', 0);

// Veritabanı Bağlantı Bilgileri
define('DB_HOST', 'localhost');
define('DB_NAME', 'betasan_app');       // cPanel veritabanı adınız (örn: kadi_betasan)
define('DB_USER', 'root');              // cPanel veritabanı kullanıcınız
define('DB_PASS', '');                  // cPanel veritabanı şifreniz
define('DB_CHARSET', 'utf8mb4');

// Betasan İletişim Bilgileri (WhatsApp Sipariş Hattı ve Sipariş E-Postası)
define('BETASAN_WHATSAPP', '905000000000'); // Ülke kodu ile birlikte (Örn: 905321234567)
define('BETASAN_EMAIL', 'siparis@betasan.com.tr');

// Otomatik Base URL Tespiti (Görsel ve API linkleri için)
$protocol = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off' || $_SERVER['SERVER_PORT'] == 443) ? "https://" : "http://";
$host = $_SERVER['HTTP_HOST'] ?? 'localhost';
$scriptDir = dirname($_SERVER['SCRIPT_NAME'] ?? '');
// Normalize script dir
$baseDir = rtrim(str_replace(['/api', '/admin'], '', $scriptDir), '/\\');
define('BASE_URL', $protocol . $host . $baseDir);
define('UPLOAD_DIR', __DIR__ . '/admin/uploads/');
define('UPLOAD_URL', BASE_URL . '/admin/uploads/');

// PDO Bağlantısı
try {
    $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=" . DB_CHARSET;
    $options = [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES   => false,
    ];
    $pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
} catch (PDOException $e) {
    // API çağrısı ise JSON dön
    if (strpos($_SERVER['REQUEST_URI'] ?? '', '/api/') !== false) {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode([
            'success' => false,
            'message' => 'Veritabanı bağlantı hatası: ' . $e->getMessage()
        ], JSON_UNESCAPED_UNICODE);
        exit;
    } else {
        die("Veritabanı bağlantı hatası: " . $e->getMessage());
    }
}

// Ortak Yardımcı Fonksiyonlar
function jsonResponse($success, $data = null, $message = '') {
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'success' => $success,
        'message' => $message,
        'data'    => $data
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

function getImageUrl($imageName) {
    if (empty($imageName)) {
        return BASE_URL . '/admin/uploads/default-product.png';
    }
    if (strpos($imageName, 'http://') === 0 || strpos($imageName, 'https://') === 0) {
        return $imageName;
    }
    return UPLOAD_URL . $imageName;
}
?>
