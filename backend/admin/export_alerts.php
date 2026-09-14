<?php
require_once __DIR__ . '/header.php';

$msg = '';

// Alarm Kapatma
if (isset($_GET['resolve'])) {
    $resId = (int)$_GET['resolve'];
    $pdo->prepare("UPDATE export_alerts SET is_resolved = 1 WHERE id = ?")->execute([$resId]);
    header("Location: export_alerts.php");
    exit;
}

// Telegram Ayarlarını Kaydetme
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'save_telegram') {
    $token = trim($_POST['bot_token'] ?? '');
    $chatId = trim($_POST['chat_id'] ?? '');

    $pdo->prepare("INSERT INTO export_settings (`key`, `value`) VALUES ('telegram_bot_token', ?) ON DUPLICATE KEY UPDATE `value`=?")->execute([$token, $token]);
    $pdo->prepare("INSERT INTO export_settings (`key`, `value`) VALUES ('telegram_chat_id', ?) ON DUPLICATE KEY UPDATE `value`=?")->execute([$chatId, $chatId]);

    if (isset($_POST['test_msg']) && !empty($token) && !empty($chatId)) {
        $testText = "🔔 *Betasan İhracat Asistanı Test Bildirimi*\n\nTelegram entegrasyonu başarıyla sağlandı! Unutulan evraklar ve cut-off süreleri için buradan bildirim alacaksınız.";
        $url = "https://api.telegram.org/bot{$token}/sendMessage?chat_id={$chatId}&text=" . urlencode($testText) . "&parse_mode=Markdown";
        @file_get_contents($url);
        $msg = 'Ayarlar kaydedildi ve cep telefonunuza test mesajı gönderildi!';
    } else {
        $msg = 'Ayarlar kaydedildi.';
    }
}

// Manuel Kural Motorunu Çalıştırma
if (isset($_GET['check_now'])) {
    require_once __DIR__ . '/../api/export_cron_checker.php';
    $msg = 'Kurallar çalıştırıldı ve uyarılar kontrol edildi.';
}

// Ayarları Çek
$settingsStmt = $pdo->query("SELECT `key`, `value` FROM export_settings");
$settings = $settingsStmt->fetchAll(PDO::FETCH_KEY_PAIR);

// Alarmları Çek
$alertStmt = $pdo->query("
    SELECT a.*, s.file_no, s.customer_name, s.country 
    FROM export_alerts a
    LEFT JOIN export_shipments s ON a.shipment_id = s.id
    WHERE a.is_resolved = 0
    ORDER BY a.severity = 'danger' DESC, a.id DESC
");
$alerts = $alertStmt->fetchAll();
?>

<div class="space-y-6">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
            <div class="flex items-center space-x-3">
                <h1 class="text-2xl font-black text-slate-800 tracking-tight">Akıllı Bildirim & Uyarı Merkezi</h1>
                <span class="bg-rose-100 text-rose-800 text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">Otomasyon</span>
            </div>
            <p class="text-sm text-slate-500 mt-1">İhracatların cut-off süreleri, geciken evraklar ve kargo hatırlatmaları burada listelenir.</p>
        </div>
        <div class="flex items-center space-x-3">
            <a href="export_alerts.php?check_now=1" class="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2.5 rounded-xl shadow transition text-sm">
                <i class="fa-solid fa-rotate"></i>
                <span>Şimdi Kuralları Çalıştır & Alarmları Yenile</span>
            </a>
        </div>
    </div>

    <?php if ($msg): ?>
    <div class="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl font-bold"><?php echo htmlspecialchars($msg); ?></div>
    <?php endif; ?>

    <!-- Telegram Entegrasyonu -->
    <div class="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm">
        <div class="flex items-center space-x-3 mb-4">
            <div class="w-10 h-10 rounded-2xl bg-sky-500 text-white flex items-center justify-center text-xl shadow-md"><i class="fa-brands fa-telegram"></i></div>
            <div>
                <h2 class="font-bold text-slate-900 text-base">Telegram Cep Bildirim Botu Entegrasyonu</h2>
                <p class="text-xs text-slate-500">Unutulan evraklar ve cut-off uyarıları anında cebinize Telegram mesajı olarak gelsin.</p>
            </div>
        </div>

        <form action="export_alerts.php" method="POST" class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <input type="hidden" name="action" value="save_telegram">
            <div>
                <label class="block font-bold text-slate-700 mb-1">Telegram Bot Token</label>
                <input type="text" name="bot_token" value="<?php echo htmlspecialchars($settings['telegram_bot_token'] ?? ''); ?>" placeholder="Örn: 7123456789:AAHx..." class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none font-mono">
            </div>
            <div>
                <label class="block font-bold text-slate-700 mb-1">Telegram Chat ID</label>
                <input type="text" name="chat_id" value="<?php echo htmlspecialchars($settings['telegram_chat_id'] ?? ''); ?>" placeholder="Örn: 987654321" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none font-mono">
            </div>
            <div class="flex items-end space-x-2">
                <button type="submit" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow transition">Kaydet</button>
                <button type="submit" name="test_msg" value="1" class="px-4 py-2 bg-sky-100 hover:bg-sky-200 text-sky-800 font-bold rounded-xl transition">Test Mesajı Gönder</button>
            </div>
        </form>
    </div>

    <!-- Aktif Alarmlar -->
    <div class="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="p-6 border-b border-slate-100 flex items-center justify-between">
            <h2 class="text-lg font-black text-slate-900">Müdahale Bekleyen Alarmlar</h2>
            <span class="text-xs font-bold px-3 py-1 bg-rose-50 text-rose-700 border border-rose-100 rounded-full"><?php echo count($alerts); ?> Aktif Alarm</span>
        </div>

        <div class="divide-y divide-slate-100">
            <?php if (!empty($alerts)): ?>
                <?php foreach ($alerts as $a): ?>
                <div class="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 <?php echo $a['severity'] == 'danger' ? 'bg-rose-50/40' : 'bg-amber-50/30'; ?>">
                    <div class="flex items-start space-x-3.5 flex-1">
                        <div class="w-10 h-10 rounded-2xl flex items-center justify-center text-lg flex-shrink-0 <?php echo $a['severity'] == 'danger' ? 'bg-rose-100 text-rose-600' : 'bg-amber-100 text-amber-600'; ?>">
                            <?php if ($a['alert_type'] == 'cutoff_approaching'): ?><i class="fa-regular fa-clock"></i>
                            <?php elseif ($a['alert_type'] == 'overdue_task'): ?><i class="fa-solid fa-circle-exclamation"></i>
                            <?php elseif ($a['alert_type'] == 'courier_missing'): ?><i class="fa-solid fa-box-open"></i>
                            <?php else: ?><i class="fa-solid fa-triangle-exclamation"></i><?php endif; ?>
                        </div>
                        <div class="space-y-1">
                            <div class="flex items-center space-x-2">
                                <span class="font-bold text-sm text-slate-900"><?php echo htmlspecialchars($a['title']); ?></span>
                                <span class="text-[10px] font-mono bg-white border border-slate-200 text-slate-600 px-2 py-0.5 rounded font-bold"><?php echo htmlspecialchars($a['file_no']); ?></span>
                            </div>
                            <p class="text-xs text-slate-600 leading-relaxed"><?php echo htmlspecialchars($a['message']); ?></p>
                            <span class="text-[10px] text-slate-400 block pt-1"><i class="fa-regular fa-calendar mr-1"></i><?php echo $a['created_at']; ?> tespit edildi</span>
                        </div>
                    </div>

                    <div class="flex items-center space-x-2 text-xs">
                        <a href="export_detail.php?id=<?php echo $a['shipment_id']; ?>" class="px-3.5 py-2 bg-white border border-slate-200 hover:border-blue-500 hover:text-blue-700 text-slate-700 font-bold rounded-xl shadow-xs transition">
                            <i class="fa-solid fa-file-lines mr-1"></i>Dosyaya Git
                        </a>
                        <a href="export_alerts.php?resolve=<?php echo $a['id']; ?>" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow transition">
                            <i class="fa-solid fa-check mr-1"></i>Kapat
                        </a>
                    </div>
                </div>
                <?php endforeach; ?>
            <?php else: ?>
            <div class="p-12 text-center text-slate-400">
                <i class="fa-solid fa-shield-check text-emerald-500 text-5xl mb-3"></i>
                <h3 class="font-bold text-slate-700 text-base">Harika! Bekleyen Kritik Bir Alarm Yok</h3>
                <p class="text-xs text-slate-400 mt-1">Tüm ihracat evrakları ve cut-off süreleri planlanan takvimde ilerliyor.</p>
            </div>
            <?php endif; ?>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/footer.php'; ?>
