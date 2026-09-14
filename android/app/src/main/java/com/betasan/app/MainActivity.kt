package com.betasan.app

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.betasan.app.data.api.ApiClient
import com.betasan.app.data.cart.CartManager
import com.betasan.app.databinding.ActivityMainBinding
import com.betasan.app.ui.cart.CartActivity
import com.betasan.app.ui.catalog.CatalogFragment
import com.betasan.app.ui.home.HomeFragment
import com.betasan.app.ui.notifications.NotificationsFragment
import com.betasan.app.ui.offers.OffersFragment
import com.betasan.app.service.ExportWorkScheduler
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val homeFragment = HomeFragment()
    private val catalogFragment = CatalogFragment()
    private val offersFragment = OffersFragment()
    private val notificationsFragment = NotificationsFragment()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ApiClient.init(this)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupNavigation()
        setupCartButton()
        observeCart()
        setupServerConfigDialog()
        registerDeviceForNotifications()

        // Arka planda 2-6 saatlik periyodik ihracat takipçisini otomatik başlat
        ExportWorkScheduler.schedulePeriodicCheck(this)

        // Eğer bildirimden gelinmişse Bildirimler ekranına yönlendir
        if (intent.getBooleanExtra("from_export_notification", false)) {
            binding.bottomNavigation.selectedItemId = R.id.navigation_notifications
        }

        // Başlangıç ekranı olarak HomeFragment yükle
        if (savedInstanceState == null) {
            binding.tvSectionBadge.text = "VİTRİN"
            loadFragment(homeFragment)
        }
    }

    private fun setupNavigation() {
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.navigation_home -> {
                    binding.tvSectionBadge.text = "VİTRİN"
                    loadFragment(homeFragment)
                    true
                }
                R.id.navigation_catalog -> {
                    binding.tvSectionBadge.text = "KATALOG"
                    loadFragment(catalogFragment)
                    true
                }
                R.id.navigation_offers -> {
                    binding.tvSectionBadge.text = "FIRSATLAR"
                    loadFragment(offersFragment)
                    true
                }
                R.id.navigation_notifications -> {
                    binding.tvSectionBadge.text = "BİLDİRİMLER"
                    loadFragment(notificationsFragment)
                    true
                }
                else -> false
            }
        }
    }

    private fun setupServerConfigDialog() {
        binding.tvSectionBadge.setOnLongClickListener {
            showServerDialog()
            true
        }
    }

    private fun showServerDialog() {
        val input = EditText(this).apply {
            setText(ApiClient.BASE_URL)
            setSelection(text.length)
            setPadding(48, 32, 48, 32)
        }
        AlertDialog.Builder(this)
            .setTitle("Admin Sunucu Bağlantısı")
            .setMessage("Bilgisayarınızın yerel IP adresini veya cPanel API adresini giriniz (Örn: http://192.168.1.50:5000/api/):")
            .setView(input)
            .setPositiveButton("Kaydet & Bağlan") { _, _ ->
                val newUrl = input.text.toString().trim()
                if (newUrl.isNotEmpty()) {
                    ApiClient.updateBaseUrl(this, newUrl)
                    Toast.makeText(this, "Sunucu güncellendi: $newUrl", Toast.LENGTH_SHORT).show()
                    val currentId = binding.bottomNavigation.selectedItemId
                    binding.bottomNavigation.selectedItemId = currentId
                }
            }
            .setNegativeButton("İptal", null)
            .show()
    }

    private fun setupCartButton() {
        binding.btnCartHeader.setOnClickListener {
            startActivity(Intent(this, CartActivity::class.java))
        }
    }

    private fun observeCart() {
        CartManager.getInstance(this).cartCount.observe(this) { count ->
            if (count > 0) {
                binding.tvCartBadge.text = count.toString()
                binding.tvCartBadge.visibility = View.VISIBLE
            } else {
                binding.tvCartBadge.visibility = View.GONE
            }
        }
    }

    private fun loadFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragmentContainer, fragment)
            .commit()
    }

    fun navigateToCatalogWithCategory(categoryId: Int?) {
        binding.bottomNavigation.selectedItemId = R.id.navigation_catalog
        catalogFragment.selectCategory(categoryId)
    }

    fun navigateToOffers() {
        binding.bottomNavigation.selectedItemId = R.id.navigation_offers
    }

    private fun registerDeviceForNotifications() {
        try {
            FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
                if (task.isSuccessful) {
                    val token = task.result
                    lifecycleScope.launch {
                        try {
                            ApiClient.service.registerDevice(
                                mapOf("token" to token, "device_type" to "android")
                            )
                        } catch (e: Exception) {
                            // Offline or local testing
                        }
                    }
                }
            }
        } catch (e: Exception) {
            // FCM config optional
        }
    }

    /**
     * Kullanıcının 2 saat veya 6 saat periyodik bildirim sıklığını ayarlayabileceği diyalog
     */
    fun showExportNotificationSettingsDialog() {
        val intervals = arrayOf(
            "2 Saatte Bir (Önerilen)",
            "6 Saatte Bir",
            "12 Saatte Bir"
        )
        val hoursArray = longArrayOf(2L, 6L, 12L)
        val currentHours = ExportWorkScheduler.getSavedIntervalHours(this)
        val selectedIndex = hoursArray.indexOf(currentHours).coerceAtLeast(0)

        var chosenIndex = selectedIndex

        AlertDialog.Builder(this)
            .setTitle("⏰ İhracat Bildirim Sıklığı")
            .setMessage("Uygulama arka plandan kapatılmış olsa dahi durum kontrolü yapılıp bildirim gönderilir.")
            .setSingleChoiceItems(intervals, selectedIndex) { _, which ->
                chosenIndex = which
            }
            .setPositiveButton("Kaydet & Başlat") { _, _ ->
                val selectedHours = hoursArray[chosenIndex]
                ExportWorkScheduler.setIntervalHours(this, selectedHours)
                Toast.makeText(this, "Bildirim sıklığı: ${selectedHours} saatte bir olarak ayarlandı!", Toast.LENGTH_SHORT).show()
            }
            .setNeutralButton("Şimdi Test Et") { _, _ ->
                ExportWorkScheduler.triggerImmediateCheck(this)
                Toast.makeText(this, "İhracat kontrolü başlatıldı, test bildirimi gönderiliyor...", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Pil Muafiyeti") { _, _ ->
                ExportWorkScheduler.requestIgnoreBatteryOptimizations(this)
            }
            .show()
    }
}
