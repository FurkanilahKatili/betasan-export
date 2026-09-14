<?php
/**
 * Betasan İhracat Akıllı Kontrol & Bildirim Motoru (Cron Script)
 * cPanel Cron Görevi olarak saat başı veya sabahları (örn: 08:30) tetiklenebilir:
 * php -q /home/username/public_html/api/export_cron_checker.php
 */

header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../db_config.php';
require_once __DIR__ . '/../admin/fcm_helper.php';

$now = new DateTime();
$nowStr = $now->format('Y-m-d H:i:s');
$todayStr = $now->format('Y-m-d');

$generatedAlerts = [];

try {
    // 1. Aktif Sevkiyatları Çek
    $stmt = $pdo->query("SELECT * FROM export_shipments WHERE status NOT IN ('completed', 'delivered')");
    $shipments = $stmt->fetchAll();

    foreach ($shipments as $s) {
        $sId = (int)$s['id'];
        $fileNo = $s['file_no'];
        $custName = $s['customer_name'];
        $country = $s['country'];

        // Görevleri Çek
        $tStmt = $pdo->prepare("SELECT * FROM export_tasks WHERE shipment_id = ?");
        $tStmt->execute([$sId]);
        $tasks = $tStmt->fetchAll();

        // Kural 1: Cut-off Yaklaşıyor / Geçti mi?
        if (!empty($s['cutoff_datetime'])) {
            $cutoffDt = new DateTime($s['cutoff_datetime']);
            $diffHours = ($cutoffDt->getTimestamp() - $now->getTimestamp()) / 3600;

            $uncompletedCritical = array_filter($tasks, fn($t) => $t['is_completed'] == 0 && in_array($t['category'], ['customs', 'transport', 'document']));

            if (!empty($uncompletedCritical)) {
                if ($diffHours > 0 && $diffHours <= 48) {
                    $sev = $diffHours <= 24 ? 'danger' : 'warning';
                    $title = "🚨 Cut-Off Yaklaşıyor: {$fileNo}";
                    $msg = "{$custName} ({$country}) yüklemesinin cut-off zamanına " . (int)$diffHours . " saat kaldı! Bekleyen kritik evraklar var.";
                    recordPhpAlert($pdo, $sId, null, 'cutoff_approaching', $sev, $title, $msg, $generatedAlerts);
                } elseif ($diffHours < 0 && in_array($s['status'], ['preparing', 'customs'])) {
                    $title = "⚠️ Cut-Off Süresi Doldu: {$fileNo}";
                    $msg = "{$custName} liman kapanış tarihi aşıldı fakat yükleme henüz yola çıkmadı!";
                    recordPhpAlert($pdo, $sId, null, 'cutoff_overdue', 'danger', $title, $msg, $generatedAlerts);
                }
            }
        }

        // Kural 2: Kalkış (ETD) Öncesi Eksik Evrak
        if (!empty($s['etd'])) {
            $etdDt = new DateTime($s['etd']);
            $diffDays = ($etdDt->getTimestamp() - $now->getTimestamp()) / 86400;

            if ($diffDays >= 0 && $diffDays <= 2) {
                foreach ($tasks as $t) {
                    if ($t['is_completed'] == 0 && $t['priority'] === 'urgent') {
                        $title = "⏳ Kalkışa " . (int)$diffDays . " Gün Kaldı - Eksik Evrak: {$t['title']}";
                        $msg = "{$fileNo} ({$custName}) sevkiyatının kalkışına çok az kaldı fakat '{$t['title']}' henüz tamamlanmadı!";
                        recordPhpAlert($pdo, $sId, (int)$t['id'], 'missing_doc', 'danger', $title, $msg, $generatedAlerts);
                    }
                }
            }
        }

        // Kural 3: Süresi Geçmiş Görev (Overdue Task)
        foreach ($tasks as $t) {
            if ($t['is_completed'] == 0 && !empty($t['due_datetime'])) {
                $dueDt = new DateTime($t['due_datetime']);
                if ($now > $dueDt) {
                    $title = "🔴 Geciken Görev: {$t['title']}";
                    $msg = "{$fileNo} ({$custName}) dosyasındaki '{$t['title']}' için son tarih aşıldı!";
                    recordPhpAlert($pdo, $sId, (int)$t['id'], 'overdue_task', 'danger', $title, $msg, $generatedAlerts);
                }
            }
        }

        // Kural 4: Yolda ve Orijinal Evrak Kargo Takip Kodu Girilmemiş
        if ($s['status'] === 'in_transit') {
            foreach ($tasks as $t) {
                if (($t['category'] === 'courier' || strpos($t['title'], 'Kargo') !== false) && $t['is_completed'] == 0 && empty($t['tracking_code'])) {
                    $title = "📦 Orijinal Evraklar Kargolandı mı? ({$fileNo})";
                    $msg = "{$custName} sevkiyatı yolda. Müşteriye asıl evrakların kargolanıp takip numarasının girilmesi gerekiyor.";
                    recordPhpAlert($pdo, $sId, (int)$t['id'], 'courier_missing', 'warning', $title, $msg, $generatedAlerts);
                }
            }
        }
    }

    // Telegram Bildirimi Tetikle
    if (!empty($generatedAlerts)) {
        $stStmt = $pdo->query("SELECT `key`, `value` FROM export_settings");
        $sets = $stStmt->fetchAll(PDO::FETCH_KEY_PAIR);
        $token = $sets['telegram_bot_token'] ?? '';
        $chatId = $sets['telegram_chat_id'] ?? '';

        if (!empty($token) && !empty($chatId)) {
            foreach (array_slice($generatedAlerts, 0, 3) as $ga) {
                $tMsg = "⚠️ *{$ga['title']}*\n\n{$ga['message']}";
                $tUrl = "https://api.telegram.org/bot{$token}/sendMessage?chat_id={$chatId}&text=" . urlencode($tMsg) . "&parse_mode=Markdown";
                @file_get_contents($tUrl);
            }
        }

        // Mobil Cihazlara FCM Push Tetikle
        $first = $generatedAlerts[0];
        sendFcmPushNotification($pdo, $first['title'], $first['message'], ['type' => 'ihracat']);
    }

    echo json_encode([
        'success' => true,
        'checked_shipments' => count($shipments),
        'new_alerts' => count($generatedAlerts),
        'alerts' => $generatedAlerts
    ], JSON_UNESCAPED_UNICODE);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'message' => $e->getMessage()], JSON_UNESCAPED_UNICODE);
}

function recordPhpAlert($pdo, $shipmentId, $taskId, $alertType, $severity, $title, $msg, &$generatedList) {
    // Daha önce çözülmemiş aynı alarm var mı kontrol et
    $chk = $pdo->prepare("SELECT id, is_resolved FROM export_alerts WHERE shipment_id = ? AND alert_type = ? AND (task_id = ? OR (task_id IS NULL AND ? IS NULL)) ORDER BY id DESC LIMIT 1");
    $chk->execute([$shipmentId, $alertType, $taskId, $taskId]);
    $row = $chk->fetch();

    if ($row && $row['is_resolved'] == 0) {
        return; // Zaten bildirilmiş ve açık
    }

    $ins = $pdo->prepare("INSERT INTO export_alerts (shipment_id, task_id, alert_type, severity, title, message, is_resolved) VALUES (?, ?, ?, ?, ?, ?, 0)");
    $ins->execute([$shipmentId, $taskId, $alertType, $severity, $title, $msg]);

    // Mobil notifications tablosuna ekle
    try {
        $nIns = $pdo->prepare("INSERT INTO notifications (title, message, notif_type) VALUES (?, ?, 'ihracat')");
        $nIns->execute([$title, $msg]);
    } catch (Exception $ex) {
        $nIns = $pdo->prepare("INSERT INTO notifications (title, message) VALUES (?, ?)");
        $nIns->execute([$title, $msg]);
    }

    $generatedList[] = [
        'shipment_id' => $shipmentId,
        'task_id' => $taskId,
        'alert_type' => $alertType,
        'title' => $title,
        'message' => $msg
    ];
}
?>
