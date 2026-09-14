<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../db_config.php';

try {
    $stmt = $pdo->query("SELECT n.*, p.name as product_name, p.image as product_image 
                         FROM notifications n 
                         LEFT JOIN products p ON n.target_product_id = p.id 
                         ORDER BY n.id DESC LIMIT 50");
    $rows = $stmt->fetchAll();

    $notifications = [];
    foreach ($rows as $row) {
        $notifications[] = [
            'id'                => (int)$row['id'],
            'title'             => $row['title'],
            'message'           => $row['message'],
            'target_product_id' => $row['target_product_id'] ? (int)$row['target_product_id'] : null,
            'product_name'      => $row['product_name'] ?? null,
            'product_image_url' => !empty($row['product_image']) ? getImageUrl($row['product_image']) : null,
            'sent_at'           => $row['sent_at']
        ];
    }

    jsonResponse(true, $notifications, 'Bildirimler getirildi.');
} catch (Exception $e) {
    jsonResponse(false, null, 'Hata: ' . $e->getMessage());
}
?>
