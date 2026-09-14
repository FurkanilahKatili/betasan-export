# Betasan Android Mobil Uygulaması

Bu klasör, Betasan için hazırlanan B2B / Dijital Katalog ve Sepet uygulamasının Android Studio (Kotlin) kaynak kodlarını içerir.

---

## 1. Android Studio'da Projeyi Açma

1. **Android Studio**'yu açın.
2. Ana ekranda **"Open"** (Aç) butonuna tıklayın.
3. Şu klasörü seçip açın:  
   `c:\Users\Furkan.Ovaciklioglu\.gemini\antigravity\scratch\Betasan Uygulaması\android`
4. Android Studio projeyi otomatik olarak tanıyacak ve Gradle yapılandırmasını başlatacaktır.

---

## 2. cPanel API Adresinizi Tanımlama

Uygulamanın cPanel'deki veritabanınızla konuşabilmesi için:
1. `app/src/main/java/com/betasan/app/data/api/ApiClient.kt` dosyasını açın.
2. `BASE_URL` değişkenine cPanel'e yüklediğiniz sitenizin API adresini yazın:
   ```kotlin
   var BASE_URL: String = "https://siteniz.com/api/" // veya https://siteniz.com/backend/api/
   ```
3. Aynı dosyada varsayılan WhatsApp ve E-Posta adreslerini de güncelleyebilirsiniz:
   ```kotlin
   const val DEFAULT_WHATSAPP_NUMBER = "90532xxxxxxx"
   const val DEFAULT_EMAIL_ADDRESS = "siparis@betasan.com.tr"
   ```

---

## 3. Uygulamayı Kendi Telefonunuzda Çalıştırma

1. Android telefonunuzda **Ayarlar -> Geliştirici Seçenekleri -> USB Hata Ayıklama (USB Debugging)** özelliğini açın.
2. Telefonunuzu USB kablosuyla bilgisayara bağlayın.
3. Android Studio'nun üst çubuğundaki cihaz listesinde kendi telefonunuzu seçin.
4. Yeşil **"Run" (Oynat)** butonuna tıklayın. Uygulama otomatik olarak telefonunuza yüklenecek ve açılacaktır!

---

## 4. Öne Çıkan Özellikler

* **Ödemesiz E-Ticaret Deneyimi:** Ürün vitrini, kategoriler, arama ve indirim rozetleri.
* **Sepet Sistemi:** Müşteri ürünleri adet seçerek sepete ekleyebilir, sepette miktarı değiştirebilir.
* **WhatsApp Sipariş Yönlendirmesi:** Tek tıkla formatlı ve düzenli bir sipariş listesini Betasan yetkilisine WhatsApp mesajı olarak açar.
* **E-Posta Teklif İletimi:** Aynı listeyi e-posta uygulaması üzerinden gönderir.
* **cPanel Senkronizasyonu:** İletilen tüm sepet talepleri cPanel veritabanına ve web paneline anında düşer.
* **Push Bildirimleri:** Admin web panelinden indirim bildirimi gönderildiğinde telefonun bildirim çubuğunda anlık bildirim gösterilir.
