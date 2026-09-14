package com.betasan.app.service

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

/**
 * İhracat Bildirimlerinin Arka Planda 2 veya 6 Saatte Bir Otomatik Çalışmasını Yöneten Zamanlayıcı.
 */
object ExportWorkScheduler {

    private const val UNIQUE_WORK_NAME = "betasan_periodic_export_tracker"
    private const val PREFS_NAME = "betasan_export_prefs"
    private const val KEY_INTERVAL_HOURS = "export_interval_hours"
    private const val KEY_ENABLED = "export_tracking_enabled"

    const val DEFAULT_INTERVAL_HOURS = 2L // Varsayılan: 2 Saatte bir

    fun getSavedIntervalHours(context: Context): Long {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getLong(KEY_INTERVAL_HOURS, DEFAULT_INTERVAL_HOURS)
    }

    fun isTrackingEnabled(context: Context): Boolean {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getBoolean(KEY_ENABLED, true)
    }

    fun setTrackingEnabled(context: Context, enabled: Boolean) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putBoolean(KEY_ENABLED, enabled).apply()
        if (enabled) {
            schedulePeriodicCheck(context, getSavedIntervalHours(context), replace = true)
        } else {
            cancelPeriodicCheck(context)
        }
    }

    fun setIntervalHours(context: Context, hours: Long) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putLong(KEY_INTERVAL_HOURS, hours).apply()
        if (isTrackingEnabled(context)) {
            schedulePeriodicCheck(context, hours, replace = true)
        }
    }

    /**
     * Android WorkManager ile periyodik kontrol planlar.
     * Uygulama arka plandan kapatılsa dahi sistem tarafından belirtilen saatte bir çalıştırılır.
     */
    fun schedulePeriodicCheck(context: Context, intervalHours: Long = DEFAULT_INTERVAL_HOURS, replace: Boolean = false) {
        if (!isTrackingEnabled(context)) return

        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED) // İnternet varken çalış
            .build()

        val periodicWorkRequest = PeriodicWorkRequestBuilder<ExportStatusWorker>(
            intervalHours, TimeUnit.HOURS,
            15, TimeUnit.MINUTES // 15 dakika esneklik penceresi (Android pil tasarrufu için)
        )
            .setConstraints(constraints)
            .build()

        val policy = if (replace) ExistingPeriodicWorkPolicy.UPDATE else ExistingPeriodicWorkPolicy.KEEP

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            UNIQUE_WORK_NAME,
            policy,
            periodicWorkRequest
        )
    }

    fun cancelPeriodicCheck(context: Context) {
        WorkManager.getInstance(context).cancelUniqueWork(UNIQUE_WORK_NAME)
    }

    /**
     * Anında test bildirimi tetiklemek için tek seferlik (OneTime) çalışma başlatır.
     */
    fun triggerImmediateCheck(context: Context) {
        val oneTimeRequest = OneTimeWorkRequestBuilder<ExportStatusWorker>().build()
        WorkManager.getInstance(context).enqueueUniqueWork(
            "betasan_export_check_immediate",
            ExistingWorkPolicy.REPLACE,
            oneTimeRequest
        )
    }

    /**
     * Xiaomi, Samsung, Huawei gibi cihazlarda uygulamanın arka planda kapatıldığında
     * öldürülmesini (kill edilmesini) önlemek için Pil Optimizasyonundan Muafiyet İster.
     */
    @SuppressLint("BatteryLife")
    fun requestIgnoreBatteryOptimizations(activity: Activity) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val pm = activity.getSystemService(Context.POWER_SERVICE) as PowerManager
            val packageName = activity.packageName
            if (!pm.isIgnoringBatteryOptimizations(packageName)) {
                try {
                    val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                        data = Uri.parse("package:$packageName")
                    }
                    activity.startActivity(intent)
                } catch (e: Exception) {
                    // Cihaz izin vermiyorsa genel pil ayarlarına yönlendir
                    val fallbackIntent = Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
                    activity.startActivity(fallbackIntent)
                }
            }
        }
    }
}
