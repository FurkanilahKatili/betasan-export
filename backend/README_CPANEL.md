# Betasan - cPanel Kurulum ve Kullanım Kılavuzu

Bu klasördeki dosyalar, Betasan Mobil Uygulamasının veritabanını, yönetim panelini ve REST API servislerini içerir.

---

## 1. Veritabanının Kurulması (cPanel - phpMyAdmin)

1. **cPanel** kontrol panelinize giriş yapın.
2. **Veritabanları (Databases)** bölümünden **MySQL® Veritabanı Sihirbazı (MySQL Database Wizard)** seçeneğine tıklayın.
3. Yeni bir veritabanı adı belirleyin (Örn: `betasan_db`).
4. Yeni bir kullanıcı ve güçlü bir şifre oluşturun (Örn: `betasan_user`).
5. Kullanıcıya **Tüm Ayrıcalıkları (ALL PRIVILEGES)** vererek işlemi tamamlayın.
6. cPanel ana sayfasına dönüp **phpMyAdmin**'e girin.
7. Sol taraftan yeni oluşturduğunuz veritabanını seçin.
8. Üst menüden **İçe Aktar (Import)** sekmesine gelin.
9. `database.sql` dosyasını seçip **Git (Go)** butonuna tıklayın. Tablolarınız ve başlangıç kategorileri anında oluşacaktır.

---

## 2. Veritabanı Bağlantısının Yapılması

`backend/db_config.php` dosyasını bir metin editörü ile açın ve az önce oluşturduğunuz bilgileri yazın:

```php
define('DB_HOST', 'localhost');
define('DB_NAME', 'cpanelKullaniciAdiniz_betasan_db'); // Oluşturduğunuz veritabanı adı
define('DB_USER', 'cpanelKullaniciAdiniz_betasan_user'); // Oluşturduğunuz veritabanı kullanıcısı
define('DB_PASS', 'VeritabaniSifreniz');                 // Belirlediğiniz şifre
```

---

## 3. Dosyaların cPanel'e Yüklenmesi

1. cPanel **Dosya Yöneticisi (File Manager)** aracını açın.
2. Sitenizin ana dizinine (`public_html`) veya bir alt klasöre (Örn: `public_html/betasan/` ya da `api.betasan.com.tr`) gidin.
3. `backend` klasörünün içindeki tüm dosyaları ve alt klasörleri (`admin`, `api`, `db_config.php`) buraya yükleyin.

---

## 4. Admin Paneline Giriş ve Ürün Ekleme

1. Tarayıcınızdan şu adrese gidin:  
   `https://siteniz.com/admin/login.php` (veya alt klasöre attıysanız `https://siteniz.com/betasan/admin/login.php`)
2. Giriş Bilgileri:
   * **Kullanıcı Adı:** `admin`
   * **Şifre:** `betasan2026!`
3. Giriş yaptıktan sonra:
   * **Ürünler -> Yeni Ürün Ekle:** Ürünün fotoğrafını yükleyebilir, adını, kodunu, kategorisini, teknik açıklamasını ve indirim oranını belirleyebilirsiniz.
   * **Bildirim Gönder:** Buradan yazdığınız indirim ve duyuru başlıkları hem Android uygulamasındaki kullanıcılara push bildirim olarak iletilir hem de uygulama içindeki bildirim geçmişine işlenir.

---

## 5. API Uç Noktaları (Android Uygulamasının Bağlandığı Servisler)

* **Ürün Listesi:** `GET https://siteniz.com/api/get_products.php`
* **Kategoriler:** `GET https://siteniz.com/api/get_categories.php`
* **Ürün Detayı:** `GET https://siteniz.com/api/get_product_detail.php?id=1`
* **İndirimli Kampanyalar / Banner:** `GET https://siteniz.com/api/get_banners.php`
* **Bildirimler:** `GET https://siteniz.com/api/get_notifications.php`
* **Cihaz Kaydı (FCM):** `POST https://siteniz.com/api/register_device.php`
