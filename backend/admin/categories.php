<?php
require_once __DIR__ . '/header.php';

$error = '';
$success = '';

// Kategori Ekleme
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['add_category'])) {
    $name = trim($_POST['name'] ?? '');
    $sort_order = (int)($_POST['sort_order'] ?? 0);

    if (empty($name)) {
        $error = 'Kategori adı boş bırakılamaz.';
    } else {
        try {
            $stmt = $pdo->prepare("INSERT INTO categories (name, sort_order) VALUES (?, ?)");
            $stmt->execute([$name, $sort_order]);
            $success = 'Kategori başarıyla eklendi.';
        } catch (Exception $e) {
            $error = 'Hata: ' . $e->getMessage();
        }
    }
}

// Kategori Silme
if (isset($_GET['delete'])) {
    $deleteId = (int)$_GET['delete'];
    try {
        $stmt = $pdo->prepare("DELETE FROM categories WHERE id = ?");
        $stmt->execute([$deleteId]);
        $success = 'Kategori silindi.';
    } catch (Exception $e) {
        $error = 'Kategori silinirken hata oluştu: ' . $e->getMessage();
    }
}

// Kategorileri çek (ürün sayılarıyla birlikte)
$categories = $pdo->query("SELECT c.*, COUNT(p.id) as product_count FROM categories c LEFT JOIN products p ON c.id = p.category_id GROUP BY c.id ORDER BY c.sort_order ASC, c.name ASC")->fetchAll();
?>

<div class="space-y-6">
    <div>
        <h2 class="text-2xl font-bold text-slate-800">Kategori Yönetimi</h2>
        <p class="text-sm text-slate-500">Mobil uygulamadaki ürün gruplarını ve menü sıralamasını yönetin.</p>
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
        <!-- Yeni Kategori Ekle Formu -->
        <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 class="font-bold text-slate-800 text-base mb-4 flex items-center space-x-2">
                <i class="fa-solid fa-plus-circle text-blue-600"></i>
                <span>Yeni Kategori Ekle</span>
            </h3>

            <form method="POST" action="categories.php" class="space-y-4">
                <input type="hidden" name="add_category" value="1">
                <div>
                    <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Kategori Adı</label>
                    <input type="text" name="name" required placeholder="Örn: Medikal Flasterler"
                           class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white">
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Sıralama Önceliği</label>
                    <input type="number" name="sort_order" value="0"
                           class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white">
                    <p class="text-[11px] text-slate-400 mt-1">Düşük sayılar uygulamada en üstte listelenir.</p>
                </div>

                <button type="submit" class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm shadow-md shadow-blue-500/20 transition flex items-center justify-center space-x-2">
                    <i class="fa-solid fa-plus text-xs"></i>
                    <span>Kategoriyi Ekle</span>
                </button>
            </form>
        </div>

        <!-- Kategori Listesi Tablosu -->
        <div class="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <table class="w-full text-left text-sm text-slate-600">
                <thead class="bg-slate-50 text-slate-500 uppercase text-xs tracking-wider border-b border-slate-200">
                    <tr>
                        <th class="px-6 py-4">Sıra</th>
                        <th class="px-6 py-4">Kategori Adı</th>
                        <th class="px-6 py-4">Ürün Sayısı</th>
                        <th class="px-6 py-4 text-right">İşlem</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <?php if (empty($categories)): ?>
                        <tr>
                            <td colspan="4" class="px-6 py-8 text-center text-slate-400">Henüz kategori bulunmuyor.</td>
                        </tr>
                    <?php else: ?>
                        <?php foreach ($categories as $c): ?>
                            <tr class="hover:bg-slate-50/80 transition">
                                <td class="px-6 py-4 font-mono font-bold text-slate-400">
                                    #<?php echo $c['sort_order']; ?>
                                </td>
                                <td class="px-6 py-4 font-bold text-slate-800">
                                    <?php echo htmlspecialchars($c['name']); ?>
                                </td>
                                <td class="px-6 py-4">
                                    <span class="px-2.5 py-1 bg-blue-50 text-blue-700 text-xs font-semibold rounded-lg">
                                        <?php echo $c['product_count']; ?> Ürün
                                    </span>
                                </td>
                                <td class="px-6 py-4 text-right">
                                    <a href="categories.php?delete=<?php echo $c['id']; ?>" 
                                       onclick="return confirm('Bu kategoriyi silmek istediğinize emin misiniz?');"
                                       class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-rose-50 text-rose-600 hover:bg-rose-100 transition" 
                                       title="Sil">
                                        <i class="fa-solid fa-trash text-xs"></i>
                                    </a>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/footer.php'; ?>
