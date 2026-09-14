<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../db_config.php';

try {
    $stmt = $pdo->query("SELECT c.*, COUNT(p.id) as product_count 
                         FROM categories c 
                         LEFT JOIN products p ON c.id = p.category_id AND p.is_active = 1 
                         GROUP BY c.id 
                         ORDER BY c.sort_order ASC, c.name ASC");
    $rows = $stmt->fetchAll();

    $categories = [];
    foreach ($rows as $row) {
        $categories[] = [
            'id'            => (int)$row['id'],
            'name'          => $row['name'],
            'slug'          => $row['slug'] ?? '',
            'icon'          => $row['icon'] ?? 'folder',
            'product_count' => (int)$row['product_count']
        ];
    }

    jsonResponse(true, $categories, 'Kategoriler listelendi.');
} catch (Exception $e) {
    jsonResponse(false, null, 'Hata: ' . $e->getMessage());
}
?>
