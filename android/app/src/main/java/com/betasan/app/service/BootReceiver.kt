package com.betasan.app.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * Cihaz Açıldığında (Reboot) veya Paket Güncellendiğinde Çalışan Receiver.
 * Uygulama açılmamış olsa dahi arka plan 2-6 saatlik zamanlayıcısını otomatik kurar.
 */
class BootReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "BetasanBootReceiver"
    }

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        if (action == Intent.ACTION_BOOT_COMPLETED ||
            action == Intent.ACTION_MY_PACKAGE_REPLACED ||
            action == "android.intent.action.QUICKBOOT_POWERON" ||
            action == "com.htc.intent.action.QUICKBOOT_POWERON"
        ) {
            Log.d(TAG, "Cihaz açılışı tespit edildi ($action). İhracat takip zamanlayıcısı kuruluyor...")
            val intervalHours = ExportWorkScheduler.getSavedIntervalHours(context)
            ExportWorkScheduler.schedulePeriodicCheck(context, intervalHours, replace = true)
        }
    }
}
