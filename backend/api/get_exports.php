<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../db_config.php';

try {
    $id = isset($_GET['id']) ? (int)$_GET['id'] : 0;

    if ($id > 0) {
        $stmt = $pdo->prepare("SELECT * FROM export_shipments WHERE id = ?");
        $stmt->execute([$id]);
        $shipment = $stmt->fetch();

        if (!$shipment) {
            echo json_encode(['success' => false, 'message' => 'İhracat dosyası bulunamadı'], JSON_UNESCAPED_UNICODE);
            exit;
        }

        $taskStmt = $pdo->prepare("SELECT * FROM export_tasks WHERE shipment_id = ? ORDER BY id ASC");
        $taskStmt->execute([$id]);
        $tasks = $taskStmt->fetchAll();

        $alertStmt = $pdo->prepare("SELECT * FROM export_alerts WHERE shipment_id = ? AND is_resolved = 0");
        $alertStmt->execute([$id]);
        $alerts = $alertStmt->fetchAll();

        echo json_encode([
            'success' => true,
            'shipment' => $shipment,
            'tasks' => $tasks,
            'alerts' => $alerts
        ], JSON_UNESCAPED_UNICODE);
        exit;
    }

    // Tüm Liste
    $stmt = $pdo->query("SELECT * FROM export_shipments ORDER BY id DESC");
    $shipments = $stmt->fetchAll();

    $data = [];
    foreach ($shipments as $s) {
        $taskStmt = $pdo->prepare("SELECT COUNT(*) as total, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as done FROM export_tasks WHERE shipment_id = ?");
        $taskStmt->execute([$s['id']]);
        $stat = $taskStmt->fetch();
        $totalT = (int)($stat['total'] ?? 0);
        $doneT = (int)($stat['done'] ?? 0);

        $alertStmt = $pdo->prepare("SELECT COUNT(*) FROM export_alerts WHERE shipment_id = ? AND is_resolved = 0");
        $alertStmt->execute([$s['id']]);
        $alertCount = (int)$alertStmt->fetchColumn();

        $data[] = [
            'id' => (int)$s['id'],
            'file_no' => $s['file_no'],
            'customer_name' => $s['customer_name'],
            'country' => $s['country'],
            'destination_port' => $s['destination_port'],
            'incoterm' => $s['incoterm'],
            'transport_mode' => $s['transport_mode'],
            'carrier_forwarder' => $s['carrier_forwarder'],
            'cutoff_datetime' => $s['cutoff_datetime'],
            'etd' => $s['etd'],
            'eta' => $s['eta'],
            'status' => $s['status'],
            'total_tasks' => $totalT,
            'done_tasks' => $doneT,
            'has_alerts' => $alertCount > 0,
            'alert_count' => $alertCount
        ];
    }

    echo json_encode(['success' => true, 'data' => $data], JSON_UNESCAPED_UNICODE);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'message' => $e->getMessage()], JSON_UNESCAPED_UNICODE);
}
?>
