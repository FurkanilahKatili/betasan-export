<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once __DIR__ . '/auth_check.php';
require_once __DIR__ . '/../db_config.php';

$currentPage = basename($_SERVER['PHP_SELF']);
?>
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Betasan Yönetim Paneli</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col md:flex-row">

    <!-- Sidebar / Yan Menü -->
    <aside class="w-full md:w-64 bg-slate-900 text-white flex-shrink-0">
        <div class="p-6 border-b border-slate-800 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center font-bold text-xl shadow-lg">
                    B
                </div>
                <div>
                    <h1 class="font-bold text-lg leading-tight tracking-wide">BETASAN</h1>
                    <span class="text-xs text-slate-400 font-medium tracking-wider uppercase">Yönetim Paneli</span>
                </div>
            </div>
        </div>

        <nav class="p-4 space-y-1">
            <a href="index.php" class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 <?php echo $currentPage == 'index.php' ? 'bg-blue-600 text-white shadow-md font-semibold' : 'text-slate-400 hover:bg-slate-800 hover:text-white'; ?>">
                <i class="fa-solid fa-chart-pie w-5 text-center"></i>
                <span>Özet Durum</span>
            </a>
            <a href="products.php" class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 <?php echo ($currentPage == 'products.php' || $currentPage == 'product_add.php' || $currentPage == 'product_edit.php') ? 'bg-blue-600 text-white shadow-md font-semibold' : 'text-slate-400 hover:bg-slate-800 hover:text-white'; ?>">
                <i class="fa-solid fa-boxes-stacked w-5 text-center"></i>
                <span>Ürünler</span>
            </a>
            <a href="categories.php" class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 <?php echo $currentPage == 'categories.php' ? 'bg-blue-600 text-white shadow-md font-semibold' : 'text-slate-400 hover:bg-slate-800 hover:text-white'; ?>">
                <i class="fa-solid fa-tags w-5 text-center"></i>
                <span>Kategoriler</span>
            </a>
            <a href="inquiries.php" class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 <?php echo $currentPage == 'inquiries.php' ? 'bg-blue-600 text-white shadow-md font-semibold' : 'text-slate-400 hover:bg-slate-800 hover:text-white'; ?>">
                <i class="fa-solid fa-cart-shopping w-5 text-center"></i>
                <span>Gelen Siparişler</span>
            </a>
            <a href="exports.php" class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 <?php echo ($currentPage == 'exports.php' || $currentPage == 'export_detail.php') ? 'bg-blue-600 text-white shadow-md font-semibold' : 'text-slate-400 hover:bg-slate-800 hover:text-white'; ?>">
                <i class="fa-solid fa-ship w-5 text-center text-sky-400"></i>
                <span class="font-bold">İhracat Takip</span>
            </a>
            <a href="export_alerts.php" class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 <?php echo $currentPage == 'export_alerts.php' ? 'bg-blue-600 text-white shadow-md font-semibold' : 'text-slate-400 hover:bg-slate-800 hover:text-white'; ?>">
                <i class="fa-solid fa-triangle-exclamation w-5 text-center text-amber-400"></i>
                <span>İhracat Alarmları</span>
            </a>
            <a href="notifications.php" class="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 <?php echo $currentPage == 'notifications.php' ? 'bg-blue-600 text-white shadow-md font-semibold' : 'text-slate-400 hover:bg-slate-800 hover:text-white'; ?>">
                <i class="fa-solid fa-bell w-5 text-center"></i>
                <span>Bildirim Gönder</span>
            </a>
            <div class="pt-6 mt-6 border-t border-slate-800">
                <a href="logout.php" class="flex items-center space-x-3 px-4 py-3 rounded-xl text-rose-400 hover:bg-rose-500/10 transition duration-200">
                    <i class="fa-solid fa-arrow-right-from-bracket w-5 text-center"></i>
                    <span>Çıkış Yap</span>
                </a>
            </div>
        </nav>
    </aside>

    <!-- Ana İçerik Alanı -->
    <main class="flex-1 flex flex-col min-w-0 overflow-hidden">
        <!-- Üst Bar -->
        <header class="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-6 z-10">
            <div class="text-sm font-medium text-slate-500">
                Betasan Mobil Ürün Yönetim Sistemi
            </div>
            <div class="flex items-center space-x-4">
                <div class="flex items-center space-x-2">
                    <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
                        <?php echo strtoupper(substr($_SESSION['admin_user'] ?? 'A', 0, 1)); ?>
                    </div>
                    <span class="text-sm font-semibold text-slate-700"><?php echo htmlspecialchars($_SESSION['admin_user'] ?? 'Yönetici'); ?></span>
                </div>
            </div>
        </header>

        <!-- Sayfa İçeriği -->
        <div class="p-6 md:p-8 flex-1 overflow-y-auto">
