package com.betasan.exporttracker

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.betasan.exporttracker.data.ExportApiClient
import com.betasan.exporttracker.databinding.ActivityMainBinding
import com.betasan.exporttracker.service.ExportWorkScheduler
import com.betasan.exporttracker.ui.AlertsFragment
import com.betasan.exporttracker.ui.SettingsFragment
import com.betasan.exporttracker.ui.ShipmentsFragment
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val shipmentsFragment = ShipmentsFragment()
    private val alertsFragment = AlertsFragment()
    private val settingsFragment = SettingsFragment()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        checkNotificationPermission()
        ExportWorkScheduler.schedulePeriodicCheck(this)
        checkServerStatus()
        loadFragment(shipmentsFragment)

        binding.bottomNav.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_shipments -> loadFragment(shipmentsFragment)
                R.id.nav_alerts -> loadFragment(alertsFragment)
                R.id.nav_settings -> loadFragment(settingsFragment)
            }
            true
        }

        binding.btnRefresh.setOnClickListener {
            checkServerStatus()
            if (shipmentsFragment.isAdded && shipmentsFragment.isVisible) {
                shipmentsFragment.loadShipments()
            }
        }
    }

    private fun loadFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragmentContainer, fragment)
            .commit()
    }

    private fun checkNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.POST_NOTIFICATIONS), 101)
            }
        }
    }

    private fun checkServerStatus() {
        lifecycleScope.launch(Dispatchers.IO) {
            val baseUrl = ExportApiClient.getBaseUrl(this@MainActivity)
            val pingUrl = baseUrl.replace("/api/", "/ping")
            var isOnline = false
            try {
                val conn = URL(pingUrl).openConnection() as HttpURLConnection
                conn.connectTimeout = 5000
                conn.readTimeout = 5000
                isOnline = (conn.responseCode == 200)
                conn.disconnect()
            } catch (_: Exception) {}

            withContext(Dispatchers.Main) {
                if (isOnline) {
                    binding.tvServerStatus.text = "🟢 Canlı Sunucu Bağlı (7/24 Aktif)"
                    binding.tvServerStatus.setTextColor(ContextCompat.getColor(this@MainActivity, R.color.success_green))
                } else {
                    binding.tvServerStatus.text = "🟡 Bağlantı Kontrol Ediliyor..."
                    binding.tvServerStatus.setTextColor(ContextCompat.getColor(this@MainActivity, R.color.accent_amber))
                }
            }
        }
    }
}
