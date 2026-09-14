<?php
require_once __DIR__ . '/header.php';

// İstatistikleri çek
try {
    $totalProducts = $pdo->query("SELECT COUNT(*) FROM products")->fetchColumn();
    $discountedProducts = $pdo->query("SELECT COUNT(*) FROM products WHERE discount_rate > 0")->fetchColumn();
    $totalCategories = $pdo->query("SELECT COUNT(*) FROM categories")->fetchColumn();
    $totalNotifications = $pdo->query("SELECT COUNT(*) FROM notifications")->fetchColumn();

    // Son eklenen 5 ürün
    $stmtRecent = $pdo->query("SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id ORDER BY p.id DESC LIMIT 5");
    $recentProducts = $stmtRecent->fetchAll();

    // Son gönderilen 3 bildirim
    $stmtNotif = $pdo->query("SELECT * FROM notifications ORDER BY id DESC LIMIT 3");
    $recentNotifications = $stmtNotif->fetchAll();
} catch (Exception $e) {
    $totalProducts = 0;
    $discountedProducts = 0;
    $totalCategories = 0;
    $totalNotifications = 0;
    $recentProducts = [];
    $recentNotifications = [];
}
?>

<div class="space-y-8">
    <!-- Karşılama Banner -->
    <div class="bg-gradient-to-r from-blue-700 via-blue-600 to-cyan-600 rounded-3xl p-6 md:p-8 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
            <h2 class="text-2xl md:text-3xl font-bold tracking-tight">Hoş Geldiniz, Betasan Yöneticisi</h2>
            <p class="text-blue-100 text-sm mt-1">Mobil uygulamada gösterilen ürünleri ve kullanıcılara gidecek indirim bildirimlerini buradan anlık olarak yönetebilirsiniz.</p>
        </div>
        <div class="flex items-center space-x-3">
            <a href="product_add.php" class="px-5 py-2.5 bg-white text-blue-700 hover:bg-blue-50 font-semibold rounded-xl text-sm shadow-md transition flex items-center space-x-2">
                <i class="fa-solid fa-plus text-xs"></i>
                <span>Yeni Ürün Ekle</span>
            </a>
            <a href="notifications.php" class="px-5 py-2.5 bg-cyan-500/30 hover:bg-cyan-500/40 text-white font-semibold rounded-xl text-sm border border-white/20 transition flex items-center space-x-2">
                <i class="fa-solid fa-bell text-xs"></i>
                <span>Bildirim Gönder</span>
            </a>
        </div>
    </div>

    <!-- İstatistik Kartları -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div class="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm flex items-center justify-between">
            <div>
                <p class="text-xs font-semibold uppercase text-slate-400 tracking-wider">Toplam Ürün</p>
                <h3 class="text-3xl font-extrabold text-slate-800 mt-1"><?php echo $totalProducts; ?></h3>
                <span class="text-xs text-slate-500 mt-1 inline-block">Uygulamadaki aktif ürünler</span>
            </div>
            <div class="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-xl">
                <i class="fa-solid fa-boxes-stacked"></i>
            </div>
        </div>

        <div class="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm flex items-center justify-between">
            <div>
                <p class="text-xs font-semibold uppercase text-slate-400 tracking-wider">İndirimli Ürünler</p>
                <h3 class="text-3xl font-extrabold text-emerald-600 mt-1"><?php echo $discountedProducts; ?></h3>
                <span class="text-xs text-slate-500 mt-1 inline-block">Aktif kampanyalılar</span>
            </div>
            <div class="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl">
                <i class="fa-solid fa-percent"></i>
            </div>
        </div>

        <div class="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm flex items-center justify-between">
            <div>
                <p class="text-xs font-semibold uppercase text-slate-400 tracking-wider">Kategoriler</p>
                <h3 class="text-3xl font-extrabold text-purple-600 mt-1"><?php echo $totalCategories; ?></h3>
                <span class="text-xs text-slate-500 mt-1 inline-block">Medikal ürün grupları</span>
            </div>
            <div class="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center text-xl">
                <i class="fa-solid fa-tags"></i>
            </div>
        </div>

        <div class="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm flex items-center justify-between">
            <div>
                <p class="text-xs font-semibold uppercase text-slate-400 tracking-wider">Gönderilen Bildirimler</p>
                <h3 class="text-3xl font-extrabold text-amber-600 mt-1"><?php echo $totalNotifications; ?></h3>
                <span class="text-xs text-slate-500 mt-1 inline-block">Kullanıcılara iletilenler</span>
            </div>
            <div class="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center text-xl">
                <i class="fa-solid fa-bullhorn"></i>
            </div>
        </div>
    </div>

    <!-- İki Kolonlu İçerik Alanı -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Sol: Son Eklenen Ürünler -->
        <div class="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div class="p-6 border-b border-slate-100 flex items-center justify-between">
                <div>
                    <h3 class="font-bold text-slate-800 text-lg">Son Eklenen Ürünler</h3>
                    <p class="text-xs text-slate-400 mt-0.5">Uygulama vitrinine eklenen son medikal ürünler</p>
                </div>
                <a href="products.php" class="text-sm font-semibold text-blue-600 hover:text-blue-700">Tümünü Gör &rarr;</a>
            </div>

            <div class="divide-y divide-slate-100">
                <?php if (empty($recentProducts)): ?>
                    <div class="p-8 text-center text-slate-400 text-sm">
                        <i class="fa-solid fa-box-open text-3xl mb-2 text-slate-300"></i>
                        <p>Henüz ürün eklenmemiş.</p>
                        <a href="product_add.php" class="mt-3 inline-block text-xs font-semibold text-blue-600 hover:underline">İlk Ürünü Şimdi Ekle &rarr;</a>
                    </div>
                <?php else: ?>
                    <?php foreach ($recentProducts as $p): ?>
                        <div class="p-4 flex items-center justify-between hover:bg-slate-50/80 transition">
                            <div class="flex items-center space-x-4">
                                <img src="<?php echo htmlspecialchars(getImageUrl($p['image'])); ?>" 
                                     alt="<?php echo htmlspecialchars($p['name']); ?>" 
                                     class="w-12 h-12 rounded-xl object-cover border border-slate-200 bg-white">
                                <div>
                                    <h4 class="font-semibold text-sm text-slate-800"><?php echo htmlspecialchars($p['name']); ?></h4>
                                    <div class="flex items-center space-x-2 text-xs text-slate-400 mt-0.5">
                                        <span>Kod: <?php echo htmlspecialchars($p['code'] ?: '-'); ?></span>
                                        <span>•</span>
                                        <span><?php echo htmlspecialchars($p['category_name'] ?: 'Genel'); ?></span>
                                    </div>
                                </div>
                            </div>
                            <div>
                                <?php if ($p['discount_rate'] > 0): ?>
                                    <span class="px-2.5 py-1 bg-emerald-100 text-emerald-700 font-bold text-xs rounded-lg">
                                        %<?php echo $p['discount_rate']; ?> İndirim
                                    </span>
                                <?php else: ?>
                                    <span class="px-2.5 py-1 bg-slate-100 text-slate-600 font-medium text-xs rounded-lg">
                                        Standart
                                    </span>
                                <?php endif; ?>
                            </div>
                        </div>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>

        <!-- Sağ: Son Gönderilen Bildirimler -->
        <div class="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div class="p-6 border-b border-slate-100 flex items-center justify-between">
                <div>
                    <h3 class="font-bold text-slate-800 text-lg">Son Bildirimler</h3>
                    <p class="text-xs text-slate-400 mt-0.5">Kullanıcılara giden duyurular</p>
                </div>
                <a href="notifications.php" class="text-sm font-semibold text-blue-600 hover:text-blue-700">+ Yeni</a>
            </div>

            <div class="p-5 space-y-4">
                <?php if (empty($recentNotifications)): ?>
                    <div class="p-6 text-center text-slate-400 text-sm">
                        <i class="fa-solid fa-bell-slash text-2xl mb-2 text-slate-300"></i>
                        <p>Henüz bildirim gönderilmemiş.</p>
                        <a href="notifications.php" class="mt-2 inline-block text-xs font-semibold text-blue-600 hover:underline">İlk Bildirimi Gönder</a>
                    </div>
                <?php else: ?>
                    <?php foreach ($recentNotifications as $notif): ?>
                        <div class="p-4 rounded-xl bg-slate-50 border border-slate-100">
                            <div class="flex items-center justify-between mb-1">
                                <h5 class="font-bold text-sm text-slate-800"><?php echo htmlspecialchars($notif['title']); ?></h5>
                                <span class="text-[10px] text-slate-400"><?php echo date('d.m.Y H:i', strtotime($notif['sent_at'])); ?></span>
                            </div>
                            <p class="text-xs text-slate-600 line-clamp-2"><?php echo htmlspecialchars($notif['message']); ?></p>
                        </div>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/footer.php'; ?>
