<?php
require_once __DIR__ . '/header.php';

$success = '';
$error = '';

if (isset($_GET['delete'])) {
    $delId = (int)$_GET['delete'];
    try {
        $stmt = $pdo->prepare("DELETE FROM order_inquiries WHERE id = ?");
        $stmt->execute([$delId]);
        $success = 'Talep başarıyla silindi.';
    } catch (Exception $e) {
        $error = 'Hata: ' . $e->getMessage();
    }
}

// Talepleri listele
$inquiries = $pdo->query("SELECT * FROM order_inquiries ORDER BY id DESC")->fetchAll();
?>

<div class="space-y-6">
    <div>
        <h2 class="text-2xl font-bold text-slate-800">Gelen Sepet & Teklif Talepleri</h2>
        <p class="text-sm text-slate-500">Mobil uygulamadan müşterilerin WhatsApp veya E-Posta ile ilettiği sepet ve sipariş talepleri.</p>
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

    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="p-5 border-b border-slate-100 flex items-center justify-between">
            <h3 class="font-bold text-slate-800 text-base">Talep Listesi</h3>
            <span class="text-xs text-slate-400">Toplam: <?php echo count($inquiries); ?> Talep</span>
        </div>

        <div class="divide-y divide-slate-100">
            <?php if (empty($inquiries)): ?>
                <div class="p-12 text-center text-slate-400 text-sm">
                    <i class="fa-solid fa-cart-shopping text-3xl mb-2 text-slate-300"></i>
                    <p>Henüz gelen sipariş / teklif talebi bulunmuyor.</p>
                </div>
            <?php else: ?>
                <?php foreach ($inquiries as $inq): ?>
                    <div class="p-6 hover:bg-slate-50/80 transition flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div class="space-y-2 flex-1">
                            <div class="flex items-center space-x-3">
                                <span class="font-bold text-slate-800 text-base"><?php echo htmlspecialchars($inq['customer_name']); ?></span>
                                <span class="text-xs px-2.5 py-1 rounded-full font-semibold <?php echo $inq['channel'] === 'whatsapp' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'; ?>">
                                    <i class="<?php echo $inq['channel'] === 'whatsapp' ? 'fa-brands fa-whatsapp' : 'fa-solid fa-envelope'; ?> mr-1"></i>
                                    <?php echo strtoupper($inq['channel']); ?>
                                </span>
                                <span class="text-xs text-slate-400">• <?php echo date('d.m.Y H:i', strtotime($inq['created_at'])); ?></span>
                            </div>

                            <?php if (!empty($inq['customer_phone'])): ?>
                                <div class="text-xs text-slate-600 font-medium">
                                    <i class="fa-solid fa-phone text-slate-400 mr-1.5"></i>
                                    <span><?php echo htmlspecialchars($inq['customer_phone']); ?></span>
                                </div>
                            <?php endif; ?>

                            <!-- Sepetteki Ürünler -->
                            <div class="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs text-slate-700 font-mono whitespace-pre-line leading-relaxed max-w-2xl">
                                <?php echo htmlspecialchars($inq['items_summary']); ?>
                            </div>

                            <?php if (!empty($inq['customer_notes'])): ?>
                                <p class="text-xs text-slate-500 italic">
                                    <strong>Müşteri Notu:</strong> "<?php echo htmlspecialchars($inq['customer_notes']); ?>"
                                </p>
                            <?php endif; ?>
                        </div>

                        <div class="flex items-center space-x-2">
                            <?php if (!empty($inq['customer_phone']) && $inq['channel'] === 'whatsapp'): ?>
                                <a href="https://wa.me/<?php echo preg_replace('/[^0-9]/', '', $inq['customer_phone']); ?>" target="_blank"
                                   class="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-xs transition flex items-center space-x-1.5">
                                    <i class="fa-brands fa-whatsapp text-sm"></i>
                                    <span>Yanıtla</span>
                                </a>
                            <?php endif; ?>
                            <a href="inquiries.php?delete=<?php echo $inq['id']; ?>" 
                               onclick="return confirm('Bu sipariş talebini silmek istediğinize emin misiniz?');"
                               class="p-2 text-slate-400 hover:text-rose-600 transition" title="Sil">
                                <i class="fa-solid fa-trash text-xs"></i>
                            </a>
                        </div>
                    </div>
                <?php endforeach; ?>
            <?php endif; ?>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/footer.php'; ?>
