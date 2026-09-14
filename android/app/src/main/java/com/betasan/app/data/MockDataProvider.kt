package com.betasan.app.data

import com.betasan.app.data.model.BannerItem
import com.betasan.app.data.model.Category
import com.betasan.app.data.model.NotificationItem
import com.betasan.app.data.model.Product

object MockDataProvider {

    fun getCategories(): List<Category> = listOf(
        Category(id = 1, name = "Tıbbi Flasterler", slug = "tibbi-flasterler", product_count = 12),
        Category(id = 2, name = "Fiksasyon Bantları", slug = "fiksasyon-bantlari", product_count = 8),
        Category(id = 3, name = "Enjeksiyon & Kan Alma", slug = "enjeksiyon-kan-alma", product_count = 6),
        Category(id = 4, name = "Yara Bakım & Gazlı Bez", slug = "yara-bakim", product_count = 10),
        Category(id = 5, name = "İlk Yardım & Destek", slug = "ilk-yardim", product_count = 7)
    )

    fun getBanners(): List<BannerItem> = listOf(
        BannerItem(
            id = 1,
            title = "Yeni Nesil İpek Flasterler",
            subtitle = "Hassas ciltler için üstün tutunma ve nefes alan doku",
            badge = "%15 İndirim",
            product_id = 1
        ),
        BannerItem(
            id = 2,
            title = "Kurumsal Toplu Alım Avantajı",
            subtitle = "Hastanelere ve kliniklere özel sepet teklif fırsatları",
            badge = "Özel Fırsat",
            product_id = 2
        )
    )

    fun getProducts(): List<Product> = listOf(
        Product(
            id = 1,
            name = "Betaban İpek Tıbbi Flaster 5m x 5cm",
            code = "BT-101",
            category_id = 1,
            category_name = "Tıbbi Flasterler",
            description = "Cilt dostu çinko oksit yapışkanı ve ipek dokusu ile hassas ciltler ve cerrahi pansuman sabitlemeleri için idealdir. Enine ve boyuna kolay yırtılır, deride yapışkan kalıntısı bırakmaz.",
            image_url = null,
            discount_rate = 15,
            has_discount = true,
            is_featured = true,
            created_at = "2026-09-14"
        ),
        Product(
            id = 2,
            name = "Betafix Elastik Tıbbi Fiksasyon Bandı 10m x 10cm",
            code = "BF-205",
            category_id = 2,
            category_name = "Fiksasyon Bantları",
            description = "Hava geçirgen, esnek non-woven kumaş yapısıyla hareketli eklem bölgelerinde ve kateter sabitlemede maksimum konfor ve güvenli tutuş sağlar.",
            image_url = null,
            discount_rate = 20,
            has_discount = true,
            is_featured = true,
            created_at = "2026-09-14"
        ),
        Product(
            id = 3,
            name = "Betaseri Yuvarlak Enjeksiyon Bandı (100'lü Kutu)",
            code = "BS-310",
            category_id = 3,
            category_name = "Enjeksiyon & Kan Alma",
            description = "Aşı, kan alma ve enjeksiyon sonrası kanamayı durdurmak için emici pedli, hipoalerjenik tek kullanımlık yuvarlak enjeksiyon bandı.",
            image_url = null,
            discount_rate = 0,
            has_discount = false,
            is_featured = true,
            created_at = "2026-09-14"
        ),
        Product(
            id = 4,
            name = "Betaplast PU Su Geçirmez Şeffaf Film Flaster 10m x 5cm",
            code = "BP-404",
            category_id = 1,
            category_name = "Tıbbi Flasterler",
            description = "Su geçirmez ve bakteri bariyeri oluşturan ultra ince poliüretan film. Pansumanın ıslanmasını önlerken yaranın nefes almasını sağlar.",
            image_url = null,
            discount_rate = 10,
            has_discount = true,
            is_featured = true,
            created_at = "2026-09-14"
        ),
        Product(
            id = 5,
            name = "Betasorb Steril Gaz Kompres 7.5cm x 7.5cm (50'li)",
            code = "BG-501",
            category_id = 4,
            category_name = "Yara Bakım & Gazlı Bez",
            description = "Yüksek sıvı emiciliğine sahip %100 saf pamuk hidrofil gaz kompres. Cerrahi müdahaleler ve yara pansumanları için tek tek steril paketlenmiştir.",
            image_url = null,
            discount_rate = 0,
            has_discount = false,
            is_featured = false,
            created_at = "2026-09-14"
        ),
        Product(
            id = 6,
            name = "Betaderm Hassas Cerrahi Kağıt Flaster 5m x 2.5cm",
            code = "BD-602",
            category_id = 1,
            category_name = "Tıbbi Flasterler",
            description = "Bebek, yaşlı ve hassas ciltler için mikrogözenekli kağıt taşıyıcı. Ağrısız çıkarılır, cildi tahriş etmez.",
            image_url = null,
            discount_rate = 25,
            has_discount = true,
            is_featured = true,
            created_at = "2026-09-14"
        ),
        Product(
            id = 7,
            name = "Betastrip Steril Dikiş Kapatma Şeritleri (10 Poşet)",
            code = "BST-703",
            category_id = 4,
            category_name = "Yara Bakım & Gazlı Bez",
            description = "Küçük kesi ve yaralanmalarda dikiş atmadan yara dudaklarını birleştiren poliamid liflerle güçlendirilmiş steril şeritler.",
            image_url = null,
            discount_rate = 0,
            has_discount = false,
            is_featured = false,
            created_at = "2026-09-14"
        ),
        Product(
            id = 8,
            name = "Betasport Elastik Kendinden Yapışkanlı Koheziv Bandaj",
            code = "BK-808",
            category_id = 5,
            category_name = "İlk Yardım & Destek",
            description = "Tene ve kıllara yapışmayan, sadece kendi üzerine tutunan elastik tespit ve kompresyon bandajı.",
            image_url = null,
            discount_rate = 15,
            has_discount = true,
            is_featured = true,
            created_at = "2026-09-14"
        )
    )

    fun getNotifications(): List<NotificationItem> = listOf(
        NotificationItem(
            id = 1,
            title = "Yeni Nesil İpek Flasterler Kataloğumuza Eklendi!",
            message = "Cilt dostu Betaban İpek Tıbbi Flaster ürünümüzü inceleyebilir, sepetinize ekleyerek doğrudan teklif talebi oluşturabilirsiniz.",
            target_product_id = 1,
            product_name = "Betaban İpek Tıbbi Flaster",
            sent_at = "Bugün, 09:30"
        ),
        NotificationItem(
            id = 2,
            title = "Betafix Fiksasyon Bantlarında %20 Fırsat",
            message = "Hastanelere ve kliniklere yönelik toplu alımlarda Betafix serisi için avantajlı koşullar sunulmaktadır.",
            target_product_id = 2,
            product_name = "Betafix Elastik Tıbbi Fiksasyon Bandı",
            sent_at = "Dün, 16:45"
        )
    )
}
