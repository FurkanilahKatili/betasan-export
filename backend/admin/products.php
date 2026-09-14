<?php
require_once __DIR__ . '/header.php';

$success = '';
$error = '';

// Ürün Silme İşlemi
if (isset($_GET['delete'])) {
    $deleteId = (int)$_GET['delete'];
    try {
        // Görseli de klasörden silelim
        $stmtImg = $pdo->prepare("SELECT image FROM products WHERE id = ?");
        $stmtImg->execute([$deleteId]);
        $prodImg = $stmtImg->fetchColumn();
        if (!empty($prodImg) && file_exists(UPLOAD_DIR . $prodImg)) {
            @unlink(UPLOAD_DIR . $prodImg);
        }

        $stmtDel = $pdo->prepare("DELETE FROM products WHERE id = ?");
        $stmtDel->execute([$deleteId]);
        $success = 'Ürün başarıyla silindi.';
    } catch (Exception $e) {
        $error = 'Ürün silinirken hata oluştu: ' . $e->getMessage();
    }
}

// Ürünleri Listele
$catFilter = isset($_GET['category']) ? (int)$_GET['category'] : 0;
$search = trim($_GET['q'] ?? '');

$sql = "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE 1=1";
$params = [];

if ($catFilter > 0) {
    $sql .= " AND p.category_id = ?";
    $params[] = $catFilter;
}

if (!empty($search)) {
    $sql .= " AND (p.name LIKE ? OR p.code LIKE ? OR p.description LIKE ?)";
    $params[] = "%$search%";
    $params[] = "%$search%";
    $params[] = "%$search%";
}

$sql .= " ORDER BY p.id DESC";

$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$products = $stmt->fetchAll();

// Kategorileri filtre açılır menüsü için çek
$categories = $pdo->query("SELECT * FROM categories ORDER BY sort_order ASC, name ASC")->fetchAll();
?>

<div class="space-y-6">
    <!-- Başlık & Yeni Ekle Butonu -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
            <h2 class="text-2xl font-bold text-slate-800">Ürün Yönetimi</h2>
            <p class="text-sm text-slate-500">Mobil uygulamada görünen medikal ürünleri listeleyin, düzenleyin veya yeni ekleyin.</p>
        </div>
        <a href="product_add.php" class="inline-flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm shadow-md shadow-blue-500/20 transition">
            <i class="fa-solid fa-plus text-xs"></i>
            <span>Yeni Ürün Ekle</span>
        </a>
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

    <!-- Arama ve Filtreleme Barı -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center gap-3">
        <form method="GET" action="products.php" class="flex-1 flex flex-col md:flex-row items-center gap-3 w-full">
            <div class="relative flex-1 w-full">
                <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                    <i class="fa-solid fa-search"></i>
                </span>
                <input type="text" name="q" value="<?php echo htmlspecialchars($search); ?>" placeholder="Ürün adı, ürün kodu veya açıklama ara..."
                       class="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white">
            </div>

            <select name="category" class="w-full md:w-56 py-2.5 px-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="0">Tüm Kategoriler</option>
                <?php foreach ($categories as $cat): ?>
                    <option value="<?php echo $cat['id']; ?>" <?php echo $catFilter == $cat['id'] ? 'selected' : ''; ?>>
                        <?php echo htmlspecialchars($cat['name']); ?>
                    </option>
                <?php endforeach; ?>
            </select>

            <button type="submit" class="w-full md:w-auto px-5 py-2.5 bg-slate-800 hover:bg-slate-900 text-white font-medium rounded-xl text-sm transition">
                Filtrele
            </button>
            <?php if (!empty($search) || $catFilter > 0): ?>
                <a href="products.php" class="w-full md:w-auto px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-600 text-center font-medium rounded-xl text-sm transition">
                    Temizle
                </a>
            <?php endif; ?>
        </form>
    </div>

    <!-- Ürün Tablosu -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
            <table class="w-full text-left text-sm text-slate-600">
                <thead class="bg-slate-50 text-slate-500 uppercase text-xs tracking-wider border-b border-slate-200">
                    <tr>
                        <th class="px-6 py-4">Görsel</th>
                        <th class="px-6 py-4">Ürün Bilgisi</th>
                        <th class="px-6 py-4">Kategori</th>
                        <th class="px-6 py-4">İndirim Oranı</th>
                        <th class="px-6 py-4">Durum</th>
                        <th class="px-6 py-4 text-right">İşlemler</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <?php if (empty($products)): ?>
                        <tr>
                            <td colspan="6" class="px-6 py-12 text-center text-slate-400">
                                <i class="fa-solid fa-box-open text-3xl mb-2 text-slate-300"></i>
                                <p>Kayıtlı ürün bulunamadı.</p>
                            </td>
                        </tr>
                    <?php else: ?>
                        <?php foreach ($products as $p): ?>
                            <tr class="hover:bg-slate-50/80 transition">
                                <td class="px-6 py-4">
                                    <img src="<?php echo htmlspecialchars(getImageUrl($p['image'])); ?>" 
                                         alt="<?php echo htmlspecialchars($p['name']); ?>" 
                                         class="w-14 h-14 rounded-xl object-cover border border-slate-200 bg-white">
                                </td>
                                <td class="px-6 py-4">
                                    <div class="font-bold text-slate-800"><?php echo htmlspecialchars($p['name']); ?></div>
                                    <div class="text-xs text-slate-400 mt-0.5">Kod: <span class="font-mono text-slate-600"><?php echo htmlspecialchars($p['code'] ?: 'Yok'); ?></span></div>
                                    <p class="text-xs text-slate-500 mt-1 line-clamp-1 max-w-xs"><?php echo htmlspecialchars($p['description']); ?></p>
                                </td>
                                <td class="px-6 py-4">
                                    <span class="px-2.5 py-1 bg-slate-100 text-slate-700 font-medium text-xs rounded-lg">
                                        <?php echo htmlspecialchars($p['category_name'] ?: 'Genel'); ?>
                                    </span>
                                </td>
                                <td class="px-6 py-4">
                                    <?php if ($p['discount_rate'] > 0): ?>
                                        <span class="px-3 py-1 bg-emerald-100 text-emerald-800 font-bold text-xs rounded-full">
                                            %<?php echo $p['discount_rate']; ?> İndirim
                                        </span>
                                    <?php else: ?>
                                        <span class="text-xs text-slate-400">-</span>
                                    <?php endif; ?>
                                </td>
                                <td class="px-6 py-4">
                                    <?php if ($p['is_active']): ?>
                                        <span class="inline-flex items-center space-x-1 text-emerald-600 font-semibold text-xs">
                                            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                                            <span>Yayında</span>
                                        </span>
                                    <?php else: ?>
                                        <span class="inline-flex items-center space-x-1 text-slate-400 font-semibold text-xs">
                                            <span class="w-2 h-2 rounded-full bg-slate-300"></span>
                                            <span>Pasif</span>
                                        </span>
                                    <?php endif; ?>
                                </td>
                                <td class="px-6 py-4 text-right space-x-2">
                                    <a href="product_edit.php?id=<?php echo $p['id']; ?>" 
                                       class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition" 
                                       title="Düzenle">
                                        <i class="fa-solid fa-pen-to-square text-xs"></i>
                                    </a>
                                    <a href="products.php?delete=<?php echo $p['id']; ?>" 
                                       onclick="return confirm('Bu ürünü silmek istediğinize emin misiniz?');"
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
