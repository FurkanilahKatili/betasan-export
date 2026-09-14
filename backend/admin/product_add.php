<?php
require_once __DIR__ . '/header.php';

$error = '';
$success = '';

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
    $imageName = null;

    if (empty($name)) {
        $error = 'Ürün adı zorunludur!';
    } else {
        // Görsel Yükleme Kontrolü
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
                $imageName = 'product_' . time() . '_' . rand(100, 999) . '.' . $fileExt;
                $targetFile = UPLOAD_DIR . $imageName;
                if (!move_uploaded_file($fileTmp, $targetFile)) {
                    $error = 'Görsel yüklenirken bir sunucu hatası oluştu.';
                }
            }
        }

        if (empty($error)) {
            try {
                $stmt = $pdo->prepare("INSERT INTO products (name, code, category_id, description, image, discount_rate, is_featured, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
                $stmt->execute([$name, $code, $category_id, $description, $imageName, $discount_rate, $is_featured, $is_active]);
                $success = 'Ürün başarıyla eklendi ve uygulamada yayına alındı!';
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
            <h2 class="text-2xl font-bold text-slate-800">Yeni Ürün Ekle</h2>
            <p class="text-sm text-slate-500">Mobil uygulama kataloğuna yeni bir Betasan medikal ürünü ekleyin.</p>
        </div>
        <a href="products.php" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-xl text-sm transition flex items-center space-x-2">
            <i class="fa-solid fa-arrow-left text-xs"></i>
            <span>Ürün Listesine Dön</span>
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

    <form method="POST" action="product_add.php" enctype="multipart/form-data" class="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 md:p-8 space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Ürün Adı -->
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Ürün Adı <span class="text-rose-500">*</span></label>
                <input type="text" name="name" required placeholder="Örn: Betaban İpek Flaster 5cm x 5m"
                       class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white">
            </div>

            <!-- Ürün Kodu -->
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Ürün / Stok Kodu</label>
                <input type="text" name="code" placeholder="Örn: BT-1025"
                       class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white font-mono">
            </div>

            <!-- Kategori -->
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Kategori</label>
                <select name="category_id" class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">-- Kategori Seçin --</option>
                    <?php foreach ($categories as $cat): ?>
                        <option value="<?php echo $cat['id']; ?>"><?php echo htmlspecialchars($cat['name']); ?></option>
                    <?php endforeach; ?>
                </select>
            </div>

            <!-- İndirim Oranı -->
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">İndirim Oranı (%)</label>
                <div class="relative">
                    <input type="number" name="discount_rate" min="0" max="100" value="0" placeholder="0"
                           class="w-full pl-4 pr-10 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white">
                    <span class="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 font-bold">%</span>
                </div>
                <p class="text-xs text-slate-400 mt-1">İndirim tanımlarsanız ürün üzerinde kırmızı indirim rozeti görünecektir.</p>
            </div>
        </div>

        <!-- Açıklama -->
        <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2">Ürün Açıklaması ve Teknik Detaylar</label>
            <textarea name="description" rows="4" placeholder="Ürün özellikleri, kullanım alanları, paket içi adet, ölçü ve standartlar..."
                      class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white"></textarea>
        </div>

        <!-- Ürün Görseli -->
        <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2">Ürün Görseli</label>
            <div class="border-2 border-dashed border-slate-200 hover:border-blue-400 rounded-2xl p-6 text-center transition cursor-pointer bg-slate-50/50">
                <i class="fa-solid fa-cloud-arrow-up text-3xl text-slate-400 mb-2"></i>
                <p class="text-sm font-semibold text-slate-700">Fotoğraf seçmek için tıklayın veya sürükleyin</p>
                <p class="text-xs text-slate-400 mt-1">PNG, JPG veya WEBP (Maksimum 5MB)</p>
                <input type="file" name="image" accept="image/*" class="mt-4 block mx-auto text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
            </div>
        </div>

        <!-- Durum ve Öne Çıkarma Seçenekleri -->
        <div class="flex flex-wrap gap-6 pt-2">
            <label class="inline-flex items-center space-x-3 cursor-pointer">
                <input type="checkbox" name="is_active" value="1" checked class="w-5 h-5 rounded text-blue-600 focus:ring-blue-500 border-slate-300">
                <span class="text-sm font-semibold text-slate-700">Ürünü uygulamada yayına al</span>
            </label>

            <label class="inline-flex items-center space-x-3 cursor-pointer">
                <input type="checkbox" name="is_featured" value="1" class="w-5 h-5 rounded text-blue-600 focus:ring-blue-500 border-slate-300">
                <span class="text-sm font-semibold text-slate-700">Ana sayfada öne çıkar</span>
            </label>
        </div>

        <!-- Butonlar -->
        <div class="pt-4 border-t border-slate-100 flex items-center justify-end space-x-4">
            <a href="products.php" class="px-5 py-3 text-slate-600 hover:text-slate-800 text-sm font-medium transition">İptal</a>
            <button type="submit" class="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm shadow-lg shadow-blue-500/25 transition flex items-center space-x-2">
                <i class="fa-solid fa-save text-xs"></i>
                <span>Ürünü Kaydet</span>
            </button>
        </div>
    </form>
</div>

<?php require_once __DIR__ . '/footer.php'; ?>
