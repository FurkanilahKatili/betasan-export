# %100 Ücretsiz & Sıfır Kesintili Canlıya Alma Kılavuzu (0 TL)

Bu rehber, Betasan İhracat & Evrak Takip sisteminizi **tek kuruş (0 TL) ödemeden**, veritabanınızın **asla silinmeyeceği** ve sunucunuzun **hiç uyumadan 7/24 kesintisiz bildirim göndereceği** şekilde canlıya alma adımlarını içerir.

---

## 🎯 Kullanacağımız 3 Ücretsiz Servis

| Servis | Maliyet | Amacı |
| :--- | :---: | :--- |
| **1. Supabase** | 0 TL | Kalıcı Bulut Veritabanı (Sunucu resetlense bile ihracat verileriniz asla silinmez) |
| **2. Render.com** | 0 TL | Web Paneli ve Python API Sunucusu (Ücretsiz HTTPS adresi sağlar) |
| **3. UptimeRobot** | 0 TL | Asla Uyuma Sistemi (Her 10 dakikada bir `/ping` yaparak sunucuyu uyanık tutar) |

---

## ADIM 1: Ücretsiz Kalıcı Veritabanını Açma (Supabase - 2 Dakika)

Render'ın ücretsiz planında verilerin silinme riskini sıfırlamak için veritabanımızı Supabase'de tutuyoruz:

1. [supabase.com](https://supabase.com) adresine gidin ve ücretsiz bir hesap açın (GitHub veya E-posta ile).
2. **"New Project"** butonuna tıklayın:
   * **Project Name:** `betasan-export`
   * **Database Password:** Güçlü bir şifre belirleyin ve bir kenara not edin.
   * **Region:** Frankfurt (Almanya) veya size en yakın bölgeyi seçin.
3. Sol menüden **Project Settings -> Database** sekmesine gelin.
4. **Connection String -> URI** bölümündeki adresi kopyalayın (Örn: `postgresql://postgres.xxx:[SIFRENIZ]@aws-0-eu-central-1.pooler.supabase.com:5432/postgres`).
   *(Parolanızı bu linkteki `[YOUR-PASSWORD]` kısmına yazın).*

---

## ADIM 2: Web Panelini ve API'yi Yayına Alma (Render.com - 3 Dakika)

Projenizin kök dizinine gerekli olan `Procfile` ve `requirements.txt` dosyaları otomatik olarak eklendi.

1. [render.com](https://render.com) adresine gidin ve ücretsiz hesap açın.
2. **New + -> Web Service** seçeneğine tıklayın.
3. Kodlarınızı içeren GitHub deponuzu bağlayın (veya "Public Git repository" seçeneğiyle yükleyin).
4. Ayarları şu şekilde doldurun:
   * **Name:** `betasan-ihracat`
   * **Language:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn --chdir backend_local server:app`
   * **Instance Type:** `Free` (0 TL)
5. Sayfanın altındaki **Environment Variables (Ortam Değişkenleri)** bölümüne tıklayın ve şunu ekleyin:
   * **Key:** `DATABASE_URL`
   * **Value:** *(1. Adımda Supabase'den aldığınız veritabanı bağlantı linki)*
6. **"Create Web Service"** butonuna basın. 1-2 dakika içinde siteniz yayına girecektir!  
   Size özel canlı adresiniz: `https://betasan-ihracat.onrender.com`

---

## ADIM 3: "Asla Uyuma" ve Otomatik Kural Motorunu Başlatma (UptimeRobot - 1 Dakika)

Render ücretsiz servisi 15 dakika boşta kaldığında uyumasın ve her 10 dakikada bir ihracatlarınızı otomatik denetlesin:

1. [uptimerobot.com](https://uptimerobot.com) adresine gidin ve ücretsiz hesap açın.
2. **"Add New Monitor"** butonuna tıklayın:
   * **Monitor Type:** `HTTP(s)`
   * **Friendly Name:** `Betasan Uyanık Tutucu`
   * **URL (or IP):** `https://betasan-ihracat.onrender.com/ping`  *(Render adresinizin sonuna /ping ekleyin)*
   * **Monitoring Interval:** `10 minutes` (Her 10 dakikada bir)
3. **"Create Monitor"** butonuna tıklayın.

> [!TIP]
> **Mucizevi Özellik:** UptimeRobot her 10 dakikada bir `/ping` adresine istek attığında:
> 1. Render sunucunuz hiçbir zaman 15 dakikalık boşluğa düşmez, **7/24 kesintisiz açık kalır.**
> 2. Hazırladığımız `/ping` rotası arka planda **İhracat Kural Motorunu tetikler;** yaklaşan bir cut-off veya eksik evrak varsa sunucu anında cep telefonunuza veya Telegram'ınıza bildirim gönderir!

---

## ADIM 4: Android Uygulamanızı Canlı Sunucuya Bağlama

1. Telefonunuzda **Betasan Mobil Uygulamasını** açın.
2. Üst bardaki **"VİTRİN"** rozetine **uzun basın** (veya sunucu ayarı diyalogunu açın).
3. Açılan kutucuğa Render canlı adresinizi yazın:  
   `https://betasan-ihracat.onrender.com/api/`
4. **"Kaydet & Bağlan"** butonuna basın.
5. Alt menüden **Bildirimler** sekmesine gelip en üstteki **"İhracat Otomatik Bildirim Sıklığı"** kartından sıklığı **2 Saat** veya **6 Saat** olarak seçip **"Şimdi Test Et"**e dokunun.

---

## ADIM 5: Telegram Cep Bildirimini Açma (Yedek Güvence)

1. Tarayıcınızdan `https://betasan-ihracat.onrender.com/admin/exports/alerts` adresine girin.
2. **Telegram Bot Token** ve **Chat ID** alanlarını doldurun.
3. **"Test Mesajı Gönder"** butonuna basın. Telefonunuzdaki Telegram anında ötecektir!

---

## 🔒 Güvenlik & Dayanıklılık Özeti

* **Maliyet:** Tamamen 0 TL.
* **Veri Güvenliği:** Veriler Supabase bulutunda şifreli ve kalıcı olarak tutulur; sunucu resetlense dahi sıfır veri kaybı yaşanır.
* **Bildirim Güvencesi:** 
  1. Telefonunuz kapalıyken bile 2 saatte bir uyanıp sorgular.
  2. UptimeRobot her 10 dakikada bir sunucuyu tetikler, acil durumda telefona bildirim fırlatılır.
  3. Telegram botu ile yedek sesli mesaj iletilir.
