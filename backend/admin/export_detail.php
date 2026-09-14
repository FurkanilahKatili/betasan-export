<?php
require_once __DIR__ . '/header.php';

$shipmentId = (int)($_GET['id'] ?? 0);
if (!$shipmentId) {
    header("Location: exports.php");
    exit;
}

$stmt = $pdo->prepare("SELECT * FROM export_shipments WHERE id = ?");
$stmt->execute([$shipmentId]);
$s = $stmt->fetch();

if (!$s) {
    echo "<div class='p-8 text-center'>İhracat dosyası bulunamadı. <a href='exports.php' class='text-blue-600 underline'>Geri Dön</a></div>";
    require_once __DIR__ . '/footer.php';
    exit;
}

// Durum Güncelleme
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'update_status') {
    $newStatus = $_POST['status'] ?? 'preparing';
    $pdo->prepare("UPDATE export_shipments SET status = ? WHERE id = ?")->execute([$newStatus, $shipmentId]);
    header("Location: export_detail.php?id=" . $shipmentId);
    exit;
}

// Görev Tamamlama / Bekliyor Toggle
if (isset($_GET['toggle_task'])) {
    $taskId = (int)$_GET['toggle_task'];
    $chkStmt = $pdo->prepare("SELECT is_completed FROM export_tasks WHERE id = ? AND shipment_id = ?");
    $chkStmt->execute([$taskId, $shipmentId]);
    $curr = $chkStmt->fetchColumn();
    if ($curr !== false) {
        $newState = $curr == 1 ? 0 : 1;
        $compAt = $newState == 1 ? date('Y-m-d H:i') : null;
        $pdo->prepare("UPDATE export_tasks SET is_completed = ?, completed_at = ? WHERE id = ?")->execute([$newState, $compAt, $taskId]);
        if ($newState == 1) {
            $pdo->prepare("UPDATE export_alerts SET is_resolved = 1 WHERE task_id = ?")->execute([$taskId]);
        }
    }
    header("Location: export_detail.php?id=" . $shipmentId);
    exit;
}

// Görev Silme
if (isset($_GET['delete_task'])) {
    $delId = (int)$_GET['delete_task'];
    $pdo->prepare("DELETE FROM export_tasks WHERE id = ? AND shipment_id = ?")->execute([$delId, $shipmentId]);
    $pdo->prepare("DELETE FROM export_alerts WHERE task_id = ?")->execute([$delId]);
    header("Location: export_detail.php?id=" . $shipmentId);
    exit;
}

// Yeni Özel Görev Ekleme
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'add_custom_task') {
    $title = trim($_POST['title'] ?? '');
    $category = $_POST['category'] ?? 'document';
    $priority = $_POST['priority'] ?? 'normal';
    $due = !empty($_POST['due_datetime']) ? $_POST['due_datetime'] : null;
    $notes = trim($_POST['notes'] ?? '');

    if (!empty($title)) {
        $pdo->prepare("INSERT INTO export_tasks (shipment_id, title, category, priority, due_datetime, notes, is_completed) VALUES (?, ?, ?, ?, ?, ?, 0)")
            ->execute([$shipmentId, $title, $category, $priority, $due, $notes]);
    }
    header("Location: export_detail.php?id=" . $shipmentId);
    exit;
}

// Belge Dosyası & Takip No Yükleme
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'upload_doc') {
    $taskId = (int)($_POST['task_id'] ?? 0);
    $trackingCode = trim($_POST['tracking_code'] ?? '');
    $taskNotes = trim($_POST['notes'] ?? '');

    $fileUrl = null;
    if (isset($_FILES['doc_file']) && $_FILES['doc_file']['error'] === UPLOAD_ERR_OK) {
        $ext = strtolower(pathinfo($_FILES['doc_file']['name'], PATHINFO_EXTENSION));
        if (in_array($ext, ['pdf', 'png', 'jpg', 'jpeg', 'xlsx', 'docx'])) {
            $fileName = 'doc_' . $shipmentId . '_' . $taskId . '_' . time() . '.' . $ext;
            if (move_uploaded_file($_FILES['doc_file']['tmp_name'], UPLOAD_DIR . $fileName)) {
                $fileUrl = UPLOAD_URL . $fileName;
            }
        }
    }

    if ($fileUrl) {
        $pdo->prepare("UPDATE export_tasks SET document_file_url = ?, is_completed = 1, completed_at = NOW() WHERE id = ? AND shipment_id = ?")
            ->execute([$fileUrl, $taskId, $shipmentId]);
        $pdo->prepare("UPDATE export_alerts SET is_resolved = 1 WHERE task_id = ?")->execute([$taskId]);
    }
    if (!empty($trackingCode)) {
        $pdo->prepare("UPDATE export_tasks SET tracking_code = ? WHERE id = ? AND shipment_id = ?")->execute([$trackingCode, $taskId, $shipmentId]);
    }
    if (!empty($taskNotes)) {
        $pdo->prepare("UPDATE export_tasks SET notes = ? WHERE id = ? AND shipment_id = ?")->execute([$taskNotes, $taskId, $shipmentId]);
    }
    header("Location: export_detail.php?id=" . $shipmentId);
    exit;
}

// Görevleri Çek
$taskStmt = $pdo->prepare("SELECT * FROM export_tasks WHERE shipment_id = ? ORDER BY is_completed ASC, priority = 'urgent' DESC, id ASC");
$taskStmt->execute([$shipmentId]);
$tasks = $taskStmt->fetchAll();

// Alarmları Çek
$alertStmt = $pdo->prepare("SELECT * FROM export_alerts WHERE shipment_id = ? AND is_resolved = 0");
$alertStmt->execute([$shipmentId]);
$alerts = $alertStmt->fetchAll();

$totalT = count($tasks);
$doneT = count(array_filter($tasks, fn($t) => $t['is_completed'] == 1));
$pct = $totalT > 0 ? (int)(($doneT / $totalT) * 100) : 0;
?>

<div class="space-y-6">
    <!-- Geri Butonu & Başlık -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center space-x-4">
            <a href="exports.php" class="w-10 h-10 rounded-2xl bg-white border border-slate-200 text-slate-600 hover:text-blue-600 flex items-center justify-center shadow-sm transition">
                <i class="fa-solid fa-arrow-left"></i>
            </a>
            <div>
                <div class="flex items-center space-x-2">
                    <span class="text-xs font-black text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-lg border border-blue-100"><?php echo htmlspecialchars($s['file_no']); ?></span>
                    <h1 class="text-2xl font-black text-slate-800"><?php echo htmlspecialchars($s['customer_name']); ?></h1>
                </div>
                <p class="text-xs text-slate-500 mt-0.5"><i class="fa-solid fa-location-dot text-rose-500 mr-1"></i><?php echo htmlspecialchars($s['country']); ?> <?php if ($s['destination_port']) echo '&bull; ' . htmlspecialchars($s['destination_port']); ?></p>
            </div>
        </div>

        <div class="flex items-center space-x-3">
            <form action="export_detail.php?id=<?php echo $shipmentId; ?>" method="POST" class="flex items-center space-x-2">
                <input type="hidden" name="action" value="update_status">
                <select name="status" onchange="this.form.submit()" class="bg-white border border-slate-200 text-xs font-bold rounded-xl px-3 py-2 shadow-sm outline-none text-slate-700">
                    <option value="preparing" <?php echo $s['status'] == 'preparing' ? 'selected' : ''; ?>>🟡 Hazırlık Aşamasında</option>
                    <option value="customs" <?php echo $s['status'] == 'customs' ? 'selected' : ''; ?>>🟣 Gümrükleme / Tescil</option>
                    <option value="in_transit" <?php echo $s['status'] == 'in_transit' ? 'selected' : ''; ?>>🔵 Yolda / Seyir Halinde</option>
                    <option value="delivered" <?php echo $s['status'] == 'delivered' ? 'selected' : ''; ?>>🟢 Varış / Teslim Edildi</option>
                    <option value="completed" <?php echo $s['status'] == 'completed' ? 'selected' : ''; ?>>✅ Dosya Kapandı / Tamamlandı</option>
                </select>
            </form>
            <button onclick="document.getElementById('modal-add-task').classList.remove('hidden')" class="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-3.5 py-2 rounded-xl shadow-sm transition">
                <i class="fa-solid fa-plus"></i>
                <span>Özel Evrak Ekle</span>
            </button>
        </div>
    </div>

    <!-- Aktif Alarmlar Varsa -->
    <?php if (!empty($alerts)): ?>
    <div class="bg-rose-50 border border-rose-200 rounded-2xl p-4 space-y-2">
        <div class="flex items-center space-x-2 text-rose-800 font-bold text-xs">
            <i class="fa-solid fa-triangle-exclamation text-rose-600 animate-pulse text-sm"></i>
            <span>Bu sevkiyatta dikkat edilmesi gereken kritik uyarılar var:</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <?php foreach ($alerts as $a): ?>
            <div class="bg-white p-3 rounded-xl border border-rose-200/80 shadow-xs flex items-start justify-between">
                <div>
                    <div class="font-bold text-xs text-rose-900"><?php echo htmlspecialchars($a['title']); ?></div>
                    <div class="text-[11px] text-slate-600 mt-0.5"><?php echo htmlspecialchars($a['message']); ?></div>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
    <?php endif; ?>

    <!-- Bilgi Kartı -->
    <div class="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div class="space-y-2">
            <span class="text-slate-400 text-[10px] font-bold uppercase tracking-wider block">Lojistik & Taşıma</span>
            <div class="flex items-center space-x-2 text-sm font-bold text-slate-800">
                <?php if ($s['transport_mode'] == 'sea') echo '<i class="fa-solid fa-ship text-sky-600"></i> Denizyolu';
                elseif ($s['transport_mode'] == 'road') echo '<i class="fa-solid fa-truck text-amber-600"></i> Karayolu';
                else echo '<i class="fa-solid fa-plane text-violet-600"></i> Havayolu'; ?>
                <span>&bull; <?php echo htmlspecialchars($s['incoterm']); ?></span>
            </div>
            <div class="text-xs text-slate-500 font-mono"><?php echo htmlspecialchars($s['carrier_forwarder'] ?? 'Acente serbest'); ?></div>
        </div>

        <div class="space-y-1 text-xs">
            <span class="text-slate-400 text-[10px] font-bold uppercase tracking-wider block">Kritik Tarihler</span>
            <div>Cut-Off: <strong class="text-amber-900 font-mono"><?php echo htmlspecialchars($s['cutoff_datetime'] ?? 'Belirtilmedi'); ?></strong></div>
            <div>Kalkış (ETD): <strong class="text-slate-700 font-mono"><?php echo htmlspecialchars($s['etd'] ?? '-'); ?></strong></div>
            <div>Varış (ETA): <strong class="text-slate-700 font-mono"><?php echo htmlspecialchars($s['eta'] ?? '-'); ?></strong></div>
        </div>

        <div class="space-y-1 text-xs">
            <span class="text-slate-400 text-[10px] font-bold uppercase tracking-wider block">Dosya Notları</span>
            <p class="text-slate-600 line-clamp-3 italic"><?php echo htmlspecialchars($s['notes'] ?? 'Özel not bulunmuyor.'); ?></p>
        </div>

        <div class="flex flex-col justify-center bg-slate-50 p-4 rounded-2xl border border-slate-100">
            <div class="flex items-center justify-between text-xs font-bold mb-1">
                <span class="text-slate-600">Evrak Tamamlanma</span>
                <span class="<?php echo $pct == 100 ? 'text-emerald-600' : 'text-blue-700'; ?>"><?php echo $doneT; ?>/<?php echo $totalT; ?> (%<?php echo $pct; ?>)</span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                <div class="h-3 rounded-full transition-all duration-500 <?php echo $pct == 100 ? 'bg-emerald-500' : 'bg-blue-600'; ?>" style="width: <?php echo $pct; ?>%"></div>
            </div>
        </div>
    </div>

    <!-- Evrak Kontrol Listesi Matrisi -->
    <div class="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="p-6 border-b border-slate-100 flex items-center justify-between">
            <div>
                <h2 class="text-lg font-black text-slate-900">Evrak & Görev Kontrol Matrisi</h2>
                <p class="text-xs text-slate-400">Tek tıkla tamamlandı yapabilir, PDF yükleyebilir ve takip kodu girebilirsiniz.</p>
            </div>
            <span class="text-xs text-slate-400 font-mono"><?php echo $totalT; ?> Görev</span>
        </div>

        <div class="divide-y divide-slate-100">
            <?php foreach ($tasks as $t): ?>
            <div class="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/80 transition <?php echo $t['is_completed'] ? 'bg-emerald-50/30' : ''; ?>">
                <div class="flex items-start space-x-3.5 flex-1">
                    <a href="export_detail.php?id=<?php echo $shipmentId; ?>&toggle_task=<?php echo $t['id']; ?>" class="w-7 h-7 rounded-xl flex items-center justify-center transition shadow-xs <?php echo $t['is_completed'] ? 'bg-emerald-500 text-white hover:bg-emerald-600' : 'bg-slate-100 border border-slate-300 text-transparent hover:text-slate-400'; ?>">
                        <i class="fa-solid fa-check text-xs"></i>
                    </a>

                    <div class="space-y-1 flex-1">
                        <div class="flex items-center space-x-2">
                            <span class="font-bold text-sm <?php echo $t['is_completed'] ? 'line-through text-slate-400' : 'text-slate-900'; ?>"><?php echo htmlspecialchars($t['title']); ?></span>
                            <?php if ($t['priority'] === 'urgent' && !$t['is_completed']): ?>
                            <span class="bg-rose-100 text-rose-700 text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider">Acil</span>
                            <?php endif; ?>
                            <span class="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono uppercase"><?php echo htmlspecialchars($t['category']); ?></span>
                        </div>

                        <?php if ($t['notes']): ?>
                        <p class="text-xs text-slate-500"><?php echo htmlspecialchars($t['notes']); ?></p>
                        <?php endif; ?>

                        <div class="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-1">
                            <?php if ($t['due_datetime']): ?>
                            <span><i class="fa-regular fa-calendar mr-1"></i>Son: <strong class="text-slate-700 font-mono"><?php echo htmlspecialchars($t['due_datetime']); ?></strong></span>
                            <?php endif; ?>
                            <?php if ($t['tracking_code']): ?>
                            <span class="text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100 font-mono font-bold"><i class="fa-solid fa-truck-fast mr-1"></i>Takip: <?php echo htmlspecialchars($t['tracking_code']); ?></span>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>

                <div class="flex items-center space-x-2 text-xs">
                    <?php if ($t['document_file_url']): ?>
                    <a href="<?php echo htmlspecialchars($t['document_file_url']); ?>" target="_blank" class="inline-flex items-center space-x-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold px-3 py-1.5 rounded-xl border border-blue-200 transition">
                        <i class="fa-solid fa-file-arrow-down"></i>
                        <span>Belgeyi İndir</span>
                    </a>
                    <?php endif; ?>

                    <button onclick="openUploadModal('<?php echo $t['id']; ?>', '<?php echo addslashes($t['title']); ?>')" class="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold transition" title="Belge Yükle">
                        <i class="fa-solid fa-paperclip"></i>
                    </button>

                    <a href="export_detail.php?id=<?php echo $shipmentId; ?>&delete_task=<?php echo $t['id']; ?>" onclick="return confirm('Bu görevi silmek istediğinize emin misiniz?');" class="p-2 rounded-xl text-slate-400 hover:text-rose-600 transition" title="Sil">
                        <i class="fa-solid fa-trash-can"></i>
                    </a>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
</div>

<!-- BELGE YÜKLEME MODAL -->
<div id="modal-upload" class="hidden fixed inset-0 z-50 bg-slate-950/50 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 class="font-bold text-slate-900 text-sm" id="modal-upload-title">Evrak / Takip Bilgisi Ekle</h3>
            <button onclick="document.getElementById('modal-upload').classList.add('hidden')" class="text-slate-400 p-1"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <form action="export_detail.php?id=<?php echo $shipmentId; ?>" method="POST" enctype="multipart/form-data" class="space-y-4 mt-4 text-xs">
            <input type="hidden" name="action" value="upload_doc">
            <input type="hidden" name="task_id" id="upload-task-id" value="">
            <div>
                <label class="block font-bold text-slate-700 mb-1">Evrak Dosyası (PDF / Resim)</label>
                <input type="file" name="doc_file" accept=".pdf,.png,.jpg,.jpeg,.xlsx" class="w-full text-xs text-slate-500">
            </div>
            <div>
                <label class="block font-bold text-slate-700 mb-1">Kargo Takip No (Varsa)</label>
                <input type="text" name="tracking_code" placeholder="Örn: DHL 123456789" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
            </div>
            <div>
                <label class="block font-bold text-slate-700 mb-1">Not Ekle</label>
                <input type="text" name="notes" placeholder="Belge hakkında not..." class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
            </div>
            <div class="pt-3 border-t border-slate-100 flex justify-end space-x-2">
                <button type="button" onclick="document.getElementById('modal-upload').classList.add('hidden')" class="px-4 py-2 font-bold text-slate-500">Vazgeç</button>
                <button type="submit" class="px-5 py-2 font-bold bg-blue-600 text-white rounded-xl shadow transition">Kaydet</button>
            </div>
        </form>
    </div>
</div>

<!-- ÖZEL GÖREV MODAL -->
<div id="modal-add-task" class="hidden fixed inset-0 z-50 bg-slate-950/50 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 class="font-bold text-slate-900 text-sm">Özel Evrak/Görev Ekle</h3>
            <button onclick="document.getElementById('modal-add-task').classList.add('hidden')" class="text-slate-400 p-1"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <form action="export_detail.php?id=<?php echo $shipmentId; ?>" method="POST" class="space-y-4 mt-4 text-xs">
            <input type="hidden" name="action" value="add_custom_task">
            <div>
                <label class="block font-bold text-slate-700 mb-1">Evrak / Görev Başlığı *</label>
                <input type="text" name="title" required placeholder="Örn: Sağlık Bakanlığı İzin Belgesi" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-none">
            </div>
            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Kategori</label>
                    <select name="category" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
                        <option value="document">📄 Evrak</option>
                        <option value="customs">🏛️ Gümrük</option>
                        <option value="transport">🚢 Lojistik</option>
                        <option value="payment">💳 Finans</option>
                        <option value="courier">📦 Kargo</option>
                    </select>
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Öncelik</label>
                    <select name="priority" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
                        <option value="normal">Normal</option>
                        <option value="urgent">🚨 Acil</option>
                    </select>
                </div>
            </div>
            <div>
                <label class="block font-bold text-slate-700 mb-1">Son Tarih</label>
                <input type="datetime-local" name="due_datetime" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
            </div>
            <div>
                <label class="block font-bold text-slate-700 mb-1">Not / Açıklama</label>
                <input type="text" name="notes" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none">
            </div>
            <div class="pt-3 border-t border-slate-100 flex justify-end space-x-2">
                <button type="button" onclick="document.getElementById('modal-add-task').classList.add('hidden')" class="px-4 py-2 font-bold text-slate-500">Vazgeç</button>
                <button type="submit" class="px-5 py-2 font-bold bg-blue-600 text-white rounded-xl shadow transition">Görevi Ekle</button>
            </div>
        </form>
    </div>
</div>

<script>
function openUploadModal(taskId, title) {
    document.getElementById('modal-upload-title').innerText = title + ' - Evrak / Takip Ekle';
    document.getElementById('upload-task-id').value = taskId;
    document.getElementById('modal-upload').classList.remove('hidden');
}
</script>

<?php require_once __DIR__ . '/footer.php'; ?>
