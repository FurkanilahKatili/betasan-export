<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../db_config.php';

$id = isset($_GET['id']) ? (int)$_GET['id'] : 0;

if ($id <= 0) {
    jsonResponse(false, null, 'Geçersiz ürün kimliği.');
}

try {
    $stmt = $pdo->prepare("SELECT p.*, c.name as category_name 
                           FROM products p 
                           LEFT JOIN categories c ON p.category_id = c.id 
                           WHERE p.id = ? AND p.is_active = 1");
    $stmt->execute([$id]);
    $product = $stmt->fetch();

    if (!$product) {
        jsonResponse(false, null, 'Ürün bulunamadı.');
    }

    $data = [
        'id'            => (int)$product['id'],
        'name'          => $product['name'],
        'code'          => $product['code'] ?? '',
        'category_id'   => (int)$product['category_id'],
        'category_name' => $product['category_name'] ?? 'Genel',
        'description'   => $product['description'] ?? '',
        'image_url'     => getImageUrl($product['image']),
        'discount_rate' => (int)$product['discount_rate'],
        'has_discount'  => ((int)$product['discount_rate'] > 0),
        'is_featured'   => (bool)$product['is_featured'],
        'created_at'    => $product['created_at']
    ];

    // İlgili benzer ürünler (Aynı kategoriden 4 ürün)
    if (!empty($product['category_id'])) {
        $stmtRelated = $pdo->prepare("SELECT id, name, code, image, discount_rate 
                                      FROM products 
                                      WHERE category_id = ? AND id != ? AND is_active = 1 
                                      ORDER BY id DESC LIMIT 4");
        $stmtRelated->execute([$product['category_id'], $id]);
        $relatedRows = $stmtRelated->fetchAll();
        $related = [];
        foreach ($relatedRows as $r) {
            $related[] = [
                'id'            => (int)$r['id'],
                'name'          => $r['name'],
                'code'          => $r['code'] ?? '',
                'image_url'     => getImageUrl($r['image']),
                'discount_rate' => (int)$r['discount_rate'],
                'has_discount'  => ((int)$r['discount_rate'] > 0)
            ];
        }
        $data['related_products'] = $related;
    } else {
        $data['related_products'] = [];
    }

    jsonResponse(true, $data, 'Ürün detayları getirildi.');
} catch (Exception $e) {
    jsonResponse(false, null, 'Hata: ' . $e->getMessage());
}
?>
