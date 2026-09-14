<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../db_config.php';

// JSON Gövdesini Oku
$input = json_decode(file_get_contents('php://input'), true);

$token = trim($input['token'] ?? $_POST['token'] ?? '');
$deviceType = trim($input['device_type'] ?? $_POST['device_type'] ?? 'android');

if (empty($token)) {
    jsonResponse(false, null, 'Cihaz tokeni boş olamaz.');
}

try {
    // Token zaten var mı?
    $stmtCheck = $pdo->prepare("SELECT id FROM device_tokens WHERE token = ? LIMIT 1");
    $stmtCheck->execute([$token]);
    $existing = $stmtCheck->fetch();

    if (!$existing) {
        $stmtInsert = $pdo->prepare("INSERT INTO device_tokens (token, device_type) VALUES (?, ?)");
        $stmtInsert->execute([$token, $deviceType]);
    }

    jsonResponse(true, ['token' => $token], 'Cihaz tokeni başarıyla kaydedildi.');
} catch (Exception $e) {
    jsonResponse(false, null, 'Kayıt hatası: ' . $e->getMessage());
}
?>
