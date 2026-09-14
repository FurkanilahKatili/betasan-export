<?php
require_once __DIR__ . '/header.php';

$error = '';
$success = '';
$id = (int)($_GET['id'] ?? 0);

if ($id <= 0) {
    header("Location: products.php");
    exit;
}

// Mevcut ürünü çek
$stmt = $pdo->prepare("SELECT * FROM products WHERE id = ?");
$stmt->execute([$id]);
$product = $stmt->fetch();

if (!$product) {
    header("Location: products.php");
    exit;
}

// Kategorileri çek
$categories = $pdo->query("SELECT * FROM categories ORDER BY sort_order ASC, name ASC")->fetchAll();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = trim($_POST['name'] ?? '');
    $code = trim($_POST['code'] ?? '');
    $category_id = !empty($_POST['category_id']) ? (int)$_POST['category_id'] : null;
    $description = trim($_POST['description'] ?? '');
    $discount_rate = (int)($_POST['discount_rate'] ?? 0);
    $is_featured = isset($_POST['is_featured']) ? 1 : 0;
    $is_active = isset($_POST['is_active']) ? 1 : 0;
    $imageName = $product['image'];

    if (empty($name)) {
        $error = 'Ürün adı zorunludur!';
    } else {
        // Yeni görsel yüklenmiş mi?
        if (isset($_FILES['image']) && $_FILES['image']['error'] === UPLOAD_ERR_OK) {
            $fileTmp = $_FILES['image']['tmp_name'];
            $fileName = $_FILES['image']['name'];
            $fileExt = strtolower(pathinfo($fileName, PATHINFO_EXTENSION));
            $allowedExts = ['jpg', 'jpeg', 'png', 'webp'];

            if (!in_array($fileExt, $allowedExts)) {
                $error = 'Sadece JPG, JPEG, PNG veya WEBP formatında görsel yükleyebilirsiniz.';
            } else {
                if (!file_exists(UPLOAD_DIR)) {
                    mkdir(UPLOAD_DIR, 0777, true);
                }
                $newImageName = 'product_' . time() . '_' . rand(100, 999) . '.' . $fileExt;
                $targetFile = UPLOAD_DIR . $newImageName;
                if (move_uploaded_file($fileTmp, $targetFile)) {
                    // Eski görseli silelim
                    if (!empty($product['image']) && file_exists(UPLOAD_DIR . $product['image'])) {
                        @unlink(UPLOAD_DIR . $product['image']);
                    }
                    $imageName = $newImageName;
                } else {
                    $error = 'Yeni görsel yüklenirken sunucu hatası oluştu.';
                }
            }
        }

        if (empty($error)) {
            try {
                $stmtUpdate = $pdo->prepare("UPDATE products SET name = ?, code = ?, category_id = ?, description = ?, image = ?, discount_rate = ?, is_featured = ?, is_active = ? WHERE id = ?");
                $stmtUpdate->execute([$name, $code, $category_id, $description, $imageName, $discount_rate, $is_featured, $is_active, $id]);
                $success = 'Ürün bilgileri başarıyla güncellendi!';

                // Yenilenmiş halini çek
                $stmt->execute([$id]);
                $product = $stmt->fetch();
            } catch (Exception $e) {
                $error = 'Veritabanı hatası: ' . $e->getMessage();
            }
        }
    }
}
?>

<div class="max-w-4xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h2 class="text-2xl font-bold text-slate-800">Ürün Düzenle: <?php echo htmlspecialchars($product['name']); ?></h2>
            <p class="text-sm text-slate-500">Ürün detaylarını, görsellerini ve indirim oranını güncelleyin.</p>
        </div>
        <a href="products.php" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-xl text-sm transition flex items-center space-x-2">
            <i class="fa-solid fa-arrow-left text-xs"></i>
            <span>Listeye Dön</span>
        </a>
    </div>

    <?php if ($success): ?>
        <div class="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <i class="fa-solid fa-circle-check text-emerald-500"></i>
                <span><?php echo htmlspecialchars($success); ?></span>
            </div>
            <a href="products.php" class="font-semibold underline">Ürünleri Gör &rarr;</a>
        </div>
    <?php endif; ?>

    <?php if ($error): ?>
        <div class="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center space-x-3">
            <i class="fa-solid fa-circle-exclamation text-rose-500"></i>
            <span><?php echo htmlspecialchars($error); ?></span>
        </div>
    <?php endif; ?>

    <form method="POST" action="product_edit.php?id=<?php echo $id; ?>" enctype="multipart/form-data" class="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 md:p-8 space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Ürün Adı <span class="text-rose-500">*</span></label>
                <input type="text" name="name" required value="<?php echo htmlspecialchars($product['name']); ?>"
                       class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white">
            </div>

            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Ürün / Stok Kodu</label>
                <input type="text" name="code" value="<?php echo htmlspecialchars($product['code']); ?>"
                       class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white font-mono">
            </div>

            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Kategori</label>
                <select name="category_id" class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">-- Kategori Seçin --</option>
                    <?php foreach ($categories as $cat): ?>
                        <option value="<?php echo $cat['id']; ?>" <?php echo $product['category_id'] == $cat['id'] ? 'selected' : ''; ?>>
                            <?php echo htmlspecialchars($cat['name']); ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </div>

            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">İndirim Oranı (%)</label>
                <div class="relative">
                    <input type="number" name="discount_rate" min="0" max="100" value="<?php echo (int)$product['discount_rate']; ?>"
                           class="w-full pl-4 pr-10 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white">
                    <span class="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 font-bold">%</span>
                </div>
            </div>
        </div>

        <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2">Ürün Açıklaması ve Detaylar</label>
            <textarea name="description" rows="4"
                      class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white"><?php echo htmlspecialchars($product['description']); ?></textarea>
        </div>

        <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2">Ürün Görseli</label>
            <div class="flex items-center space-x-6 p-4 rounded-2xl bg-slate-50 border border-slate-200">
                <img src="<?php echo htmlspecialchars(getImageUrl($product['image'])); ?>" 
                     alt="Mevcut Görsel" class="w-20 h-20 rounded-xl object-cover border border-slate-300 bg-white">
                <div class="flex-1">
                    <p class="text-xs font-semibold text-slate-600 mb-1">Yeni bir görsel seçerek değiştirebilirsiniz:</p>
                    <input type="file" name="image" accept="image/*" class="block text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                </div>
            </div>
        </div>

        <div class="flex flex-wrap gap-6 pt-2">
            <label class="inline-flex items-center space-x-3 cursor-pointer">
                <input type="checkbox" name="is_active" value="1" <?php echo $product['is_active'] ? 'checked' : ''; ?> class="w-5 h-5 rounded text-blue-600 focus:ring-blue-500 border-slate-300">
                <span class="text-sm font-semibold text-slate-700">Ürünü uygulamada yayına al</span>
            </label>

            <label class="inline-flex items-center space-x-3 cursor-pointer">
                <input type="checkbox" name="is_featured" value="1" <?php echo $product['is_featured'] ? 'checked' : ''; ?> class="w-5 h-5 rounded text-blue-600 focus:ring-blue-500 border-slate-300">
                <span class="text-sm font-semibold text-slate-700">Ana sayfada öne çıkar</span>
            </label>
        </div>

        <div class="pt-4 border-t border-slate-100 flex items-center justify-end space-x-4">
            <a href="products.php" class="px-5 py-3 text-slate-600 hover:text-slate-800 text-sm font-medium transition">İptal</a>
            <button type="submit" class="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm shadow-lg shadow-blue-500/25 transition flex items-center space-x-2">
                <i class="fa-solid fa-save text-xs"></i>
                <span>Değişiklikleri Kaydet</span>
            </button>
        </div>
    </form>
</div>

<?php require_once __DIR__ . '/footer.php'; ?>
