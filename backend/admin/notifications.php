<?php
require_once __DIR__ . '/header.php';
require_once __DIR__ . '/fcm_helper.php';

$error = '';
$success = '';

// Bildirim Silme
if (isset($_GET['delete'])) {
    $deleteId = (int)$_GET['delete'];
    try {
        $stmt = $pdo->prepare("DELETE FROM notifications WHERE id = ?");
        $stmt->execute([$deleteId]);
        $success = 'Bildirim geçmişten silindi.';
    } catch (Exception $e) {
        $error = 'Silme hatası: ' . $e->getMessage();
    }
}

// Yeni Bildirim Gönderme
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['send_notification'])) {
    $title = trim($_POST['title'] ?? '');
    $message = trim($_POST['message'] ?? '');
    $target_product_id = !empty($_POST['target_product_id']) ? (int)$_POST['target_product_id'] : null;

    if (empty($title) || empty($message)) {
        $error = 'Bildirim başlığı ve mesajı zorunludur.';
    } else {
        try {
            // 1. Veritabanına kaydet
            $stmt = $pdo->prepare("INSERT INTO notifications (title, message, target_product_id) VALUES (?, ?, ?)");
            $stmt->execute([$title, $message, $target_product_id]);

            // 2. Cihazlara Push Gönder
            $pushResult = sendFcmPushNotification($pdo, $title, $message, [
                'product_id' => $target_product_id
            ]);

            $success = 'Bildirim başarıyla kaydedildi ve tüm mobil kullanıcılara gönderildi!';
        } catch (Exception $e) {
            $error = 'Hata: ' . $e->getMessage();
        }
    }
}

// Ürünleri açılır liste için çek
$products = $pdo->query("SELECT id, name, code FROM products WHERE is_active = 1 ORDER BY name ASC")->fetchAll();

// Kayıtlı cihaz sayısı
$registeredDevicesCount = $pdo->query("SELECT COUNT(DISTINCT token) FROM device_tokens")->fetchColumn();

// Geçmiş Bildirimler
$notifications = $pdo->query("SELECT n.*, p.name as product_name FROM notifications n LEFT JOIN products p ON n.target_product_id = p.id ORDER BY n.id DESC")->fetchAll();
?>

<div class="space-y-6">
    <div>
        <h2 class="text-2xl font-bold text-slate-800">Bildirim Gönder & Yönet</h2>
        <p class="text-sm text-slate-500">Kullanıcıların telefonlarına indirim, yeni ürün ve kampanya duyuruları gönderin.</p>
    </div>

    <!-- Cihaz Durum Bilgi Kartı -->
    <div class="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-2xl p-5 text-white shadow-md flex items-center justify-between">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center text-lg">
                <i class="fa-solid fa-mobile-screen"></i>
            </div>
            <div>
                <h4 class="font-bold text-sm">Aktif Mobil Cihaz Sayısı</h4>
                <p class="text-xs text-blue-100">Uygulamayı açıp bildirim izni veren telefonlar</p>
            </div>
        </div>
        <div class="text-2xl font-black px-4 py-1.5 bg-white/20 rounded-xl border border-white/30">
            <?php echo $registeredDevicesCount; ?> Cihaz
        </div>
    </div>

    <?php if ($success): ?>
        <div class="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm flex items-center space-x-3">
            <i class="fa-solid fa-circle-check text-emerald-500"></i>
            <span><?php echo htmlspecialchars($success); ?></span>
        </div>
    <?php endif; ?>

    <?php if ($error): ?>
        <div class="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center space-x-3">
            <i class="fa-solid fa-circle-exclamation text-rose-500"></i>
            <span><?php echo htmlspecialchars($error); ?></span>
        </div>
    <?php endif; ?>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <!-- Bildirim Oluşturma Formu -->
        <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 class="font-bold text-slate-800 text-base mb-4 flex items-center space-x-2">
                <i class="fa-solid fa-paper-plane text-blue-600"></i>
                <span>Yeni Bildirim Gönder</span>
            </h3>

            <form method="POST" action="notifications.php" class="space-y-4">
                <input type="hidden" name="send_notification" value="1">

                <div>
                    <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Bildirim Başlığı <span class="text-rose-500">*</span></label>
                    <input type="text" name="title" required placeholder="Örn: %20 İndirim Fırsatı!"
                           class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white">
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Bildirim Mesajı <span class="text-rose-500">*</span></label>
                    <textarea name="message" rows="3" required placeholder="Kullanıcıların ekranında görünecek açıklama..."
                              class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white"></textarea>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">İlgili Ürün (Opsiyonel)</label>
                    <select name="target_product_id" class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="">-- Herhangi Bir Ürüne Bağlama --</option>
                        <?php foreach ($products as $pr): ?>
                            <option value="<?php echo $pr['id']; ?>">
                                <?php echo htmlspecialchars($pr['name'] . ($pr['code'] ? ' (' . $pr['code'] . ')' : '')); ?>
                            </option>
                        <?php endforeach; ?>
                    </select>
                    <p class="text-[11px] text-slate-400 mt-1">Kullanıcı bildirime tıkladığında doğrudan bu ürünün sayfası açılır.</p>
                </div>

                <button type="submit" class="w-full py-3.5 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-semibold rounded-xl text-sm shadow-lg shadow-blue-500/25 transition flex items-center justify-center space-x-2">
                    <i class="fa-solid fa-bullhorn text-xs"></i>
                    <span>Tüm Kullanıcılara Gönder</span>
                </button>
            </form>
        </div>

        <!-- Geçmiş Gönderilen Bildirimler Listesi -->
        <div class="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="p-5 border-b border-slate-100 flex items-center justify-between">
                <h3 class="font-bold text-slate-800 text-base">Bildirim Geçmişi</h3>
                <span class="text-xs text-slate-400">Toplam: <?php echo count($notifications); ?></span>
            </div>

            <div class="divide-y divide-slate-100">
                <?php if (empty($notifications)): ?>
                    <div class="p-8 text-center text-slate-400 text-sm">Henüz bildirim geçmişi bulunmuyor.</div>
                <?php else: ?>
                    <?php foreach ($notifications as $n): ?>
                        <div class="p-5 flex items-start justify-between hover:bg-slate-50/80 transition">
                            <div class="space-y-1">
                                <div class="flex items-center space-x-2">
                                    <h4 class="font-bold text-sm text-slate-800"><?php echo htmlspecialchars($n['title']); ?></h4>
                                    <span class="text-[10px] text-slate-400">• <?php echo date('d.m.Y H:i', strtotime($n['sent_at'])); ?></span>
                                </div>
                                <p class="text-xs text-slate-600"><?php echo htmlspecialchars($n['message']); ?></p>
                                <?php if (!empty($n['product_name'])): ?>
                                    <div class="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[11px] font-semibold mt-1">
                                        <i class="fa-solid fa-link text-[10px]"></i>
                                        <span>Hedef Ürün: <?php echo htmlspecialchars($n['product_name']); ?></span>
                                    </div>
                                <?php endif; ?>
                            </div>
                            <a href="notifications.php?delete=<?php echo $n['id']; ?>" 
                               onclick="return confirm('Bu bildirimi geçmişten silmek istediğinize emin misiniz?');"
                               class="text-slate-400 hover:text-rose-600 transition p-2" title="Sil">
                                <i class="fa-solid fa-trash text-xs"></i>
                            </a>
                        </div>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/footer.php'; ?>
