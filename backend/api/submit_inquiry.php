<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../db_config.php';

$input = json_decode(file_get_contents('php://input'), true);

$customerName  = trim($input['customer_name'] ?? $_POST['customer_name'] ?? 'İsimsiz Müşteri');
$customerPhone = trim($input['customer_phone'] ?? $_POST['customer_phone'] ?? '');
$customerNotes = trim($input['customer_notes'] ?? $_POST['customer_notes'] ?? '');
$channel       = trim($input['channel'] ?? $_POST['channel'] ?? 'whatsapp');
$itemsSummary  = trim($input['items_summary'] ?? $_POST['items_summary'] ?? '');

if (empty($itemsSummary) && !empty($input['items'])) {
    $lines = [];
    foreach ($input['items'] as $item) {
        $lines[] = ($item['quantity'] ?? 1) . "x " . ($item['name'] ?? 'Ürün') . " (" . ($item['code'] ?? '') . ")";
    }
    $itemsSummary = implode("\n", $lines);
}

if (empty($itemsSummary)) {
    jsonResponse(false, null, 'Sepet içeriği boş olamaz.');
}

try {
    $stmt = $pdo->prepare("INSERT INTO order_inquiries (customer_name, customer_phone, customer_notes, channel, items_summary) VALUES (?, ?, ?, ?, ?)");
    $stmt->execute([$customerName, $customerPhone, $customerNotes, $channel, $itemsSummary]);

    $orderId = $pdo->lastInsertId();

    jsonResponse(true, [
        'order_id' => $orderId,
        'whatsapp_number' => BETASAN_WHATSAPP,
        'email_address'   => BETASAN_EMAIL
    ], 'Sipariş/teklif talebi veritabanına kaydedildi.');
} catch (Exception $e) {
    jsonResponse(false, null, 'Kayıt hatası: ' . $e->getMessage());
}
?>
