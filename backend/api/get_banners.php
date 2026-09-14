<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../db_config.php';

try {
    // İndirimdeki ve öne çıkan ürünlerden otomatik kampanya bannerları oluştur
    $stmt = $pdo->query("SELECT id, name, code, image, discount_rate 
                         FROM products 
                         WHERE is_active = 1 AND (discount_rate > 0 OR is_featured = 1) 
                         ORDER BY discount_rate DESC, id DESC LIMIT 5");
    $rows = $stmt->fetchAll();

    $banners = [];
    foreach ($rows as $row) {
        $banners[] = [
            'id'            => (int)$row['id'],
            'title'         => $row['name'],
            'subtitle'      => $row['discount_rate'] > 0 ? ('%' . $row['discount_rate'] . ' Özel İndirim Fırsatı') : 'Öne Çıkan Betasan Ürünü',
            'badge'         => $row['discount_rate'] > 0 ? ('%' . $row['discount_rate'] . ' İndirim') : 'Fırsat',
            'product_id'    => (int)$row['id'],
            'image_url'     => getImageUrl($row['image'])
        ];
    }

    jsonResponse(true, $banners, 'Bannerlar listelendi.');
} catch (Exception $e) {
    jsonResponse(false, null, 'Hata: ' . $e->getMessage());
}
?>
