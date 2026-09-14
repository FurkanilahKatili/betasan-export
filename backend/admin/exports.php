<?php
require_once __DIR__ . '/header.php';

$success = '';
$error = '';

// Yeni İhracat Dosyası Ekleme
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'add_export') {
    $fileNo = trim($_POST['file_no'] ?? '');
    $customerName = trim($_POST['customer_name'] ?? '');
    $country = trim($_POST['country'] ?? '');
    $destinationPort = trim($_POST['destination_port'] ?? '');
    $incoterm = trim($_POST['incoterm'] ?? 'FOB');
    $transportMode = trim($_POST['transport_mode'] ?? 'sea');
    $carrierForwarder = trim($_POST['carrier_forwarder'] ?? '');
    $cutoffDatetime = !empty($_POST['cutoff_datetime']) ? $_POST['cutoff_datetime'] : null;
    $etd = !empty($_POST['etd']) ? $_POST['etd'] : null;
    $eta = !empty($_POST['eta']) ? $_POST['eta'] : null;
    $notes = trim($_POST['notes'] ?? '');

    if (empty($fileNo) || empty($customerName) || empty($country)) {
        $error = 'Lütfen dosya numarası, müşteri adı ve ülke alanlarını doldurun.';
    } else {
        try {
            $stmt = $pdo->prepare("INSERT INTO export_shipments (file_no, customer_name, country, destination_port, incoterm, transport_mode, carrier_forwarder, cutoff_datetime, etd, eta, notes, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'preparing')");
            $stmt->execute([$fileNo, $customerName, $country, $destinationPort, $incoterm, $transportMode, $carrierForwarder, $cutoffDatetime, $etd, $eta, $notes]);
            $shipmentId = $pdo->lastInsertId();

            // Standart Görevleri Ekle
            $tasks = [
                ['Ticari Fatura (Commercial Invoice)', 'document', 'urgent', date('Y-m-d 17:00', strtotime('+1 day')), 'Resmi ihracat faturasının hazırlanması.'],
                ['Çeki Listesi (Packing List)', 'document', 'urgent', date('Y-m-d 18:00', strtotime('+1 day')), 'Net/Brüt kilo ve koli/palet detayları.'],
                ['Dolaşım Belgesi (Menşe / ATR / EUR.1)', 'document', 'normal', $cutoffDatetime, 'Hedef ülkeye göre gümrük muafiyet evrakı.'],
                ['İhracat Gümrük Beyannamesi Tescili', 'customs', 'urgent', $cutoffDatetime, 'Müşavir tarafından beyannamenin tescil edilmesi.'],
                ['Müşteri Ödeme / Bakiye Teyidi', 'payment', 'normal', null, 'Sevkiyat öncesi tahsilat/akreditif teyidi.'],
                ['Analiz & Kalite Sertifikaları (COA / CE)', 'document', 'normal', null, 'Betasan ürün kalite ve parti kontrol raporları.']
            ];

            if ($transportMode === 'sea') {
                $tasks[] = ['Gemi Konşimento Talimatı (BL Draft)', 'transport', 'urgent', $cutoffDatetime, 'Acenteye B/L talimatının iletilmesi.'];
                $tasks[] = ['Liman / Konteyner Cut-off Kapanış Takibi', 'transport', 'urgent', $cutoffDatetime, 'Konteynerin limana girişi ve intaç onayı.'];
                $tasks[] = ['Orijinal Konşimento (Original B/L) Alımı', 'transport', 'normal', null, 'Armatörden 3/3 asıl konşimentoların alınması.'];
            } elseif ($transportMode === 'road') {
                $tasks[] = ['CMR Karayolu Taşıma Belgesi Düzenlenmesi', 'transport', 'urgent', $cutoffDatetime, 'Tır sürücüsü ve acente kaşeli CMR belgesi.'];
                $tasks[] = ['Araç Plaka & Şoför Bilgilerinin Alınması', 'transport', 'normal', null, 'Kapı çıkışı için tır plakası ve pasaport bilgisi.'];
            } elseif ($transportMode === 'air') {
                $tasks[] = ['AWB (Air Waybill) Hava Konşimentosu Kontrolü', 'transport', 'urgent', $cutoffDatetime, 'Hava kargo acentesinden AWB taslağının onaylanması.'];
            }
            $tasks[] = ['Orijinal Evrakların Müşteriye Kargolanması', 'courier', 'urgent', null, 'DHL/FedEx ile asıl evrakların alıcıya kargolanması ve takip no kaydı.'];

            $stmtTask = $pdo->prepare("INSERT INTO export_tasks (shipment_id, title, category, priority, due_datetime, notes, is_completed) VALUES (?, ?, ?, ?, ?, ?, 0)");
            foreach ($tasks as $t) {
                $stmtTask->execute([$shipmentId, $t[0], $t[1], $t[2], $t[3], $t[4]]);
            }

            header("Location: export_detail.php?id=" . $shipmentId);
            exit;
        } catch (Exception $e) {
            $error = 'Dosya açılırken hata: ' . $e->getMessage();
        }
    }
}

// İstatistikler
$activeCount = (int)$pdo->query("SELECT COUNT(*) FROM export_shipments WHERE status NOT IN ('completed', 'delivered')")->fetchColumn();
$alertCount = (int)$pdo->query("SELECT COUNT(*) FROM export_alerts WHERE is_resolved = 0")->fetchColumn();
$urgentTaskCount = (int)$pdo->query("SELECT COUNT(*) FROM export_tasks WHERE is_completed = 0 AND priority = 'urgent'")->fetchColumn();
$completedCount = (int)$pdo->query("SELECT COUNT(*) FROM export_shipments WHERE status = 'completed'")->fetchColumn();

// Filtreler & Arama
$filter = $_GET['filter'] ?? 'all';
$search = trim($_GET['search'] ?? '');

$sql = "SELECT * FROM export_shipments WHERE 1=1";
$params = [];

if ($filter === 'sea') {
    $sql .= " AND transport_mode = 'sea' AND status != 'completed'";
} elseif ($filter === 'road') {
    $sql .= " AND transport_mode = 'road' AND status != 'completed'";
} elseif ($filter === 'completed') {
    $sql .= " AND status = 'completed'";
} elseif ($filter === 'active') {
    $sql .= " AND status NOT IN ('completed', 'delivered')";
}

if (!empty($search)) {
    $sql .= " AND (file_no LIKE ? OR customer_name LIKE ? OR country LIKE ?)";
    $params[] = "%$search%";
    $params[] = "%$search%";
    $params[] = "%$search%";
}
$sql .= " ORDER BY id DESC";
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$shipments = $stmt->fetchAll();
?>

<div class="space-y-6">
    <!-- Başlık & Butonlar -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
            <div class="flex items-center space-x-3">
                <h1 class="text-2xl font-black text-slate-800 tracking-tight">İhracat & Evrak Takip Masası</h1>
                <span class="bg-blue-100 text-blue-800 text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">Operasyon</span>
            </div>
            <p class="text-sm text-slate-500 mt-1">İhracat sevkiyatlarının evrak durumu, cut-off süreleri ve gecikme uyarılarını buradan anlık izleyin.</p>
        </div>
        <div class="flex items-center space-x-3">
            <a href="export_alerts.php" class="relative inline-flex items-center space-x-2 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 font-bold px-4 py-2.5 rounded-xl shadow-sm transition text-sm">
                <i class="fa-solid fa-bell animate-pulse"></i>
                <span>Alarmlar & Uyarılar</span>
                <?php if ($alertCount > 0): ?>
                <span class="bg-rose-600 text-white text-xs px-2 py-0.5 rounded-full font-extrabold"><?php echo $alertCount; ?></span>
                <?php endif; ?>
            </a>
            <button onclick="document.getElementById('modal-new-export').classList.remove('hidden')" class="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2.5 rounded-xl shadow-md transition text-sm">
                <i class="fa-solid fa-plus"></i>
                <span>Yeni İhracat Dosyası Aç</span>
            </button>
        </div>
    </div>

    <?php if ($error): ?>
    <div class="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl font-bold"><?php echo htmlspecialchars($error); ?></div>
    <?php endif; ?>

    <!-- KPI Kartları -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
            <div>
                <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Aktif İhracatlar</span>
                <div class="text-3xl font-black text-slate-800 mt-1"><?php echo $activeCount; ?></div>
                <span class="text-xs text-sky-600 font-medium">Devam eden sevkiyat</span>
            </div>
            <div class="w-12 h-12 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center text-xl shadow-inner"><i class="fa-solid fa-ship"></i></div>
        </div>
        <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
            <div>
                <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Bekleyen Acil Evrak</span>
                <div class="text-3xl font-black text-amber-600 mt-1"><?php echo $urgentTaskCount; ?></div>
                <span class="text-xs text-amber-600 font-medium">Onay/Yükleme bekliyor</span>
            </div>
            <div class="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center text-xl shadow-inner"><i class="fa-solid fa-file-circle-exclamation"></i></div>
        </div>
        <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
            <div>
                <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Aktif Alarmlar</span>
                <div class="text-3xl font-black text-rose-600 mt-1"><?php echo $alertCount; ?></div>
                <span class="text-xs text-rose-600 font-medium">Geciken veya yaklaşan</span>
            </div>
            <div class="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center text-xl shadow-inner"><i class="fa-solid fa-triangle-exclamation"></i></div>
        </div>
        <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
            <div>
                <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tamamlanan Dosyalar</span>
                <div class="text-3xl font-black text-emerald-600 mt-1"><?php echo $completedCount; ?></div>
                <span class="text-xs text-emerald-600 font-medium">Başarıyla teslim edildi</span>
            </div>
            <div class="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl shadow-inner"><i class="fa-solid fa-circle-check"></i></div>
        </div>
    </div>

    <!-- Filtreler & Arama -->
    <div class="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-3 rounded-2xl border border-slate-200/80 shadow-sm">
        <div class="flex items-center space-x-1.5 overflow-x-auto w-full sm:w-auto text-xs font-semibold">
            <a href="exports.php?filter=all" class="px-3.5 py-2 rounded-xl transition <?php echo $filter == 'all' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'; ?>">Tümü</a>
            <a href="exports.php?filter=active" class="px-3.5 py-2 rounded-xl transition <?php echo $filter == 'active' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'; ?>">Devam Edenler</a>
            <a href="exports.php?filter=sea" class="px-3.5 py-2 rounded-xl transition flex items-center space-x-1.5 <?php echo $filter == 'sea' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'; ?>"><i class="fa-solid fa-ship text-sky-500"></i><span>Denizyolu</span></a>
            <a href="exports.php?filter=road" class="px-3.5 py-2 rounded-xl transition flex items-center space-x-1.5 <?php echo $filter == 'road' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'; ?>"><i class="fa-solid fa-truck text-amber-500"></i><span>Karayolu</span></a>
            <a href="exports.php?filter=completed" class="px-3.5 py-2 rounded-xl transition <?php echo $filter == 'completed' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'; ?>">Tamamlananlar</a>
        </div>
        <form method="GET" class="w-full sm:w-72">
            <div class="relative">
                <input type="text" name="search" value="<?php echo htmlspecialchars($search); ?>" placeholder="Dosya no, müşteri, ülke ara..." class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 outline-none">
                <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
            </div>
        </form>
    </div>

    <!-- Kart Listesi -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <?php if (!empty($shipments)): ?>
            <?php foreach ($shipments as $s): 
                $statStmt = $pdo->prepare("SELECT COUNT(*) as total, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as done FROM export_tasks WHERE shipment_id = ?");
                $statStmt->execute([$s['id']]);
                $stat = $statStmt->fetch();
                $tot = (int)($stat['total'] ?? 0);
                $done = (int)($stat['done'] ?? 0);
                $pct = $tot > 0 ? (int)(($done / $tot) * 100) : 0;

                $alertStmt = $pdo->prepare("SELECT COUNT(*) FROM export_alerts WHERE shipment_id = ? AND is_resolved = 0");
                $alertStmt->execute([$s['id']]);
                $hasAlert = (int)$alertStmt->fetchColumn() > 0;
            ?>
            <div class="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition flex flex-col justify-between overflow-hidden">
                <?php if ($hasAlert): ?>
                <div class="bg-rose-500 text-white text-[11px] font-bold px-3 py-1 flex items-center justify-between tracking-wide animate-pulse">
                    <span><i class="fa-solid fa-triangle-exclamation mr-1.5"></i>Acil Aksiyon / Evrak Bekliyor!</span>
                    <a href="export_alerts.php" class="underline text-[10px]">İncele</a>
                </div>
                <?php endif; ?>

                <div class="p-5 flex-1">
                    <div class="flex items-start justify-between">
                        <div>
                            <span class="text-xs font-black tracking-wider text-blue-700 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-100">
                                <?php echo htmlspecialchars($s['file_no']); ?>
                            </span>
                            <h3 class="font-bold text-slate-900 text-base mt-2 leading-snug"><?php echo htmlspecialchars($s['customer_name']); ?></h3>
                            <div class="flex items-center space-x-1.5 text-xs text-slate-500 mt-1">
                                <i class="fa-solid fa-location-dot text-rose-500"></i>
                                <span><?php echo htmlspecialchars($s['country']); ?></span>
                                <?php if ($s['destination_port']): ?>
                                <span>&bull; <?php echo htmlspecialchars($s['destination_port']); ?></span>
                                <?php endif; ?>
                            </div>
                        </div>
                        <div class="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center text-lg shadow-inner">
                            <?php if ($s['transport_mode'] == 'sea'): ?><i class="fa-solid fa-ship text-sky-600"></i>
                            <?php elseif ($s['transport_mode'] == 'road'): ?><i class="fa-solid fa-truck text-amber-600"></i>
                            <?php else: ?><i class="fa-solid fa-plane text-violet-600"></i><?php endif; ?>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-100 text-xs">
                        <div class="bg-slate-50 p-2 rounded-xl">
                            <span class="text-slate-400 text-[10px] uppercase font-bold block">Teslim Şekli</span>
                            <span class="font-bold text-slate-800"><?php echo htmlspecialchars($s['incoterm']); ?></span>
                        </div>
                        <div class="bg-slate-50 p-2 rounded-xl">
                            <span class="text-slate-400 text-[10px] uppercase font-bold block">Durum</span>
                            <span class="font-bold text-blue-600"><?php echo htmlspecialchars($s['status']); ?></span>
                        </div>
                    </div>

                    <div class="mt-3 space-y-1.5 text-xs text-slate-600">
                        <?php if ($s['cutoff_datetime']): ?>
                        <div class="flex items-center justify-between bg-amber-50/70 px-2 py-1 rounded-lg border border-amber-100 text-[11px]">
                            <span class="font-semibold text-amber-900"><i class="fa-regular fa-clock mr-1 text-amber-600"></i>Cut-Off:</span>
                            <span class="font-bold text-amber-950 font-mono"><?php echo htmlspecialchars($s['cutoff_datetime']); ?></span>
                        </div>
                        <?php endif; ?>
                        <div class="flex items-center justify-between text-[11px] text-slate-500 px-1">
                            <span>Kalkış: <strong class="text-slate-700"><?php echo $s['etd'] ?? '-'; ?></strong></span>
                            <span>Varış: <strong class="text-slate-700"><?php echo $s['eta'] ?? '-'; ?></strong></span>
                        </div>
                    </div>

                    <div class="mt-4 pt-3 border-t border-slate-100">
                        <div class="flex items-center justify-between text-xs font-semibold mb-1.5">
                            <span class="text-slate-600">Evrak Hazırlığı</span>
                            <span class="<?php echo $pct == 100 ? 'text-emerald-600' : 'text-blue-700'; ?> font-bold"><?php echo $done; ?>/<?php echo $tot; ?> (%<?php echo $pct; ?>)</span>
                        </div>
                        <div class="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                            <div class="h-2.5 rounded-full transition-all duration-500 <?php echo $pct == 100 ? 'bg-emerald-500' : 'bg-blue-600'; ?>" style="width: <?php echo $pct; ?>%"></div>
                        </div>
                    </div>
                </div>

                <div class="bg-slate-50 px-5 py-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span class="text-slate-400 font-mono text-[11px]"><?php echo htmlspecialchars($s['carrier_forwarder'] ?? 'Acente serbest'); ?></span>
                    <a href="export_detail.php?id=<?php echo $s['id']; ?>" class="inline-flex items-center space-x-1.5 bg-white border border-slate-200 hover:border-blue-500 hover:text-blue-600 text-slate-700 font-bold px-3 py-1.5 rounded-xl shadow-sm transition">
                        <span>Evrakları İncele</span>
                        <i class="fa-solid fa-arrow-right text-[10px]"></i>
                    </a>
                </div>
            </div>
            <?php endforeach; ?>
        <?php else: ?>
        <div class="col-span-full bg-white rounded-2xl p-12 text-center border border-slate-200">
            <i class="fa-solid fa-ship text-slate-300 text-5xl mb-3"></i>
            <h3 class="text-base font-bold text-slate-700">Kayıtlı ihracat dosyası bulunamadı</h3>
            <button onclick="document.getElementById('modal-new-export').classList.remove('hidden')" class="mt-4 inline-flex items-center space-x-2 bg-blue-600 text-white text-xs font-bold px-4 py-2 rounded-xl">
                <i class="fa-solid fa-plus"></i>
                <span>İlk İhracatı Ekle</span>
            </button>
        </div>
        <?php endif; ?>
    </div>
</div>

<!-- YENİ İHRACAT MODAL -->
<div id="modal-new-export" class="hidden fixed inset-0 z-50 bg-slate-950/50 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl max-w-xl w-full p-6 md:p-8 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between pb-4 border-b border-slate-100">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center text-lg"><i class="fa-solid fa-file-circle-plus"></i></div>
                <div>
                    <h2 class="text-lg font-bold text-slate-900">Yeni İhracat Dosyası Aç</h2>
                    <p class="text-xs text-slate-400">Sevkiyat oluşturulduğunda evrak listesi otomatik eklenir.</p>
                </div>
            </div>
            <button onclick="document.getElementById('modal-new-export').classList.add('hidden')" class="text-slate-400 hover:text-slate-600 p-2"><i class="fa-solid fa-xmark text-lg"></i></button>
        </div>

        <form action="exports.php" method="POST" class="space-y-4 mt-5">
            <input type="hidden" name="action" value="add_export">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Dosya / Ref No *</label>
                    <input type="text" name="file_no" required placeholder="Örn: EXP-2026-004" class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Müşteri / Alıcı Unvanı *</label>
                    <input type="text" name="customer_name" required placeholder="Örn: Cairo Medical Supplies" class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Hedef Ülke *</label>
                    <input type="text" name="country" required placeholder="Örn: Almanya" class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Hedef Liman / Şehir</label>
                    <input type="text" name="destination_port" placeholder="Örn: Hamburg Limanı" class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Taşıma Şekli</label>
                    <select name="transport_mode" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                        <option value="sea">🚢 Denizyolu</option>
                        <option value="road">🚛 Karayolu</option>
                        <option value="air">✈️ Havayolu</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Teslim Şekli</label>
                    <select name="incoterm" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                        <option value="FOB">FOB</option>
                        <option value="CIF">CIF</option>
                        <option value="CFR">CFR</option>
                        <option value="EXW">EXW</option>
                        <option value="DAP">DAP</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Nakliyeci</label>
                    <input type="text" name="carrier_forwarder" placeholder="Örn: Maersk" class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Cut-off Saati</label>
                    <input type="datetime-local" name="cutoff_datetime" class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Kalkış Tarihi</label>
                    <input type="date" name="etd" class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Varış Tarihi</label>
                    <input type="date" name="eta" class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none">
                </div>
            </div>

            <div>
                <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Notlar</label>
                <textarea name="notes" rows="2" class="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none"></textarea>
            </div>

            <div class="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
                <button type="button" onclick="document.getElementById('modal-new-export').classList.add('hidden')" class="px-5 py-2.5 text-xs font-bold text-slate-500">Vazgeç</button>
                <button type="submit" class="px-6 py-2.5 text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-md transition">Kaydet ve Dosyayı Aç</button>
            </div>
        </form>
    </div>
</div>

<?php require_once __DIR__ . '/footer.php'; ?>
