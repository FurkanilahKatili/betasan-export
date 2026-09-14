<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../db_config.php';

try {
    $categoryId = isset($_GET['category_id']) ? (int)$_GET['category_id'] : 0;
    $search = trim($_GET['q'] ?? $_GET['search'] ?? '');
    $onlyDiscounted = isset($_GET['only_discounted']) && $_GET['only_discounted'] == '1';
    $featured = isset($_GET['featured']) && $_GET['featured'] == '1';
    $limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 100;

    $sql = "SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE p.is_active = 1";
    $params = [];

    if ($categoryId > 0) {
        $sql .= " AND p.category_id = ?";
        $params[] = $categoryId;
    }

    if (!empty($search)) {
        $sql .= " AND (p.name LIKE ? OR p.code LIKE ? OR p.description LIKE ?)";
        $params[] = "%$search%";
        $params[] = "%$search%";
        $params[] = "%$search%";
    }

    if ($onlyDiscounted) {
        $sql .= " AND p.discount_rate > 0";
    }

    if ($featured) {
        $sql .= " AND p.is_featured = 1";
    }

    $sql .= " ORDER BY p.is_featured DESC, p.discount_rate DESC, p.id DESC LIMIT " . max(1, min($limit, 200));

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $rows = $stmt->fetchAll();

    $products = [];
    foreach ($rows as $row) {
        $products[] = [
            'id'             => (int)$row['id'],
            'name'           => $row['name'],
            'code'           => $row['code'] ?? '',
            'category_id'    => (int)$row['category_id'],
            'category_name'  => $row['category_name'] ?? 'Genel',
            'description'    => $row['description'] ?? '',
            'image_url'      => getImageUrl($row['image']),
            'discount_rate'  => (int)$row['discount_rate'],
            'has_discount'   => ((int)$row['discount_rate'] > 0),
            'is_featured'    => (bool)$row['is_featured'],
            'created_at'     => $row['created_at']
        ];
    }

    jsonResponse(true, $products, 'Ürünler başarıyla getirildi.');
} catch (Exception $e) {
    jsonResponse(false, null, 'Hata: ' . $e->getMessage());
}
?>
