package com.betasan.app.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.media.RingtoneManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.betasan.app.MainActivity
import com.betasan.app.R
import com.betasan.app.data.api.ApiClient
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Android WorkManager Tarafından Arka Planda Çalıştırılan İhracat Kontrol İşçisi.
 * Uygulama arka plandan kapatılmış (swiped away) veya telefon yeniden başlatılmış olsa bile
 * Android İş Zamanlayıcısı (JobScheduler) tarafından 2 veya 6 saatte bir otomatik uyandırılır.
 */
class ExportStatusWorker(
    private val context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    companion object {
        const val CHANNEL_EXPORT_ALERT_ID = "betasan_export_alerts"
        const val CHANNEL_EXPORT_ALERT_NAME = "İhracat Eksik Evrak & Cut-off Alarmları"

        const val CHANNEL_EXPORT_SUMMARY_ID = "betasan_export_summary"
        const val CHANNEL_EXPORT_SUMMARY_NAME = "İhracat Periyodik Durum Özeti"

        private const val NOTIF_ID_ALERT = 2001
        private const val NOTIF_ID_SUMMARY = 2002
    }

    override suspend fun doWork(): Result {
        ApiClient.init(context)

        return try {
            // 1. Sunucudaki kural motorunu tetikle ve güncel sevkiyatları çek
            try {
                ApiClient.service.checkExportAlerts()
            } catch (e: Exception) {
                // Sunucu kural API'si başarısız olsa bile listeyi çekmeyi dene
            }

            val response = ApiClient.service.getExports()
            if (!response.success || response.data == null) {
                return Result.retry()
            }

            val shipments = response.data.filter { it.status != "completed" && it.status != "delivered" }
            if (shipments.isEmpty()) {
                // Aktif ihracat yoksa sessizce tamamla
                return Result.success()
            }

            // 2. Eksik ve geciken evrakları tespit et
            val alertShipments = shipments.filter { it.hasAlerts || it.alertCount > 0 }
            val uncompletedShipments = shipments.filter { it.doneTasks < it.totalTasks }

            if (alertShipments.isNotEmpty()) {
                // ACİL DURUM BİLDİRİMİ (Eksik evrak, cut-off veya gecikme var!)
                val urgentShipment = alertShipments.first()
                val title = "🚨 İhracat Takip: ${alertShipments.size} Sevkiyatta Kritik Evrak Eksik!"
                val message = "${urgentShipment.fileNo} (${urgentShipment.customerName}, ${urgentShipment.country}): " +
                        "${urgentShipment.doneTasks}/${urgentShipment.totalTasks} evrak hazır. Cut-off ve kalkış sürelerini kontrol edin!"

                showNotification(
                    channelId = CHANNEL_EXPORT_ALERT_ID,
                    channelName = CHANNEL_EXPORT_ALERT_NAME,
                    notifId = NOTIF_ID_ALERT,
                    title = title,
                    message = message,
                    isUrgent = true
                )
            } else if (uncompletedShipments.isNotEmpty()) {
                // HAZIRLIKTA OLAN EVRAKLAR VAR (2-6 saatlik düzenli hatırlatma)
                val first = uncompletedShipments.first()
                val title = "⏳ İhracat Hatırlatması: ${uncompletedShipments.size} Sevkiyat Hazırlıkta"
                val message = "${first.fileNo} (${first.country}): ${first.doneTasks}/${first.totalTasks} evrak tamamlandı. Unutulan bir işlem olmaması için kontrol ediniz."

                showNotification(
                    channelId = CHANNEL_EXPORT_SUMMARY_ID,
                    channelName = CHANNEL_EXPORT_SUMMARY_NAME,
                    notifId = NOTIF_ID_SUMMARY,
                    title = title,
                    message = message,
                    isUrgent = false
                )
            } else {
                // TÜM EVRAKLAR TAMAM
                val timeStr = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date())
                val title = "✅ Betasan İhracat Durumu ($timeStr)"
                val message = "Aktif ${shipments.size} ihracat sevkiyatınızın tüm evrakları takvime uygun, eksik belge bulunmuyor."

                showNotification(
                    channelId = CHANNEL_EXPORT_SUMMARY_ID,
                    channelName = CHANNEL_EXPORT_SUMMARY_NAME,
                    notifId = NOTIF_ID_SUMMARY,
                    title = title,
                    message = message,
                    isUrgent = false
                )
            }

            Result.success()
        } catch (e: Exception) {
            // Ağ hatası veya sunucuya ulaşılamıyorsa Android OS daha sonra otomatik yeniden dener
            Result.retry()
        }
    }

    private fun showNotification(
        channelId: String,
        channelName: String,
        notifId: Int,
        title: String,
        message: String,
        isUrgent: Boolean
    ) {
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        // Android 8.0+ Kanal Tanımlama
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val importance = if (isUrgent) NotificationManager.IMPORTANCE_HIGH else NotificationManager.IMPORTANCE_DEFAULT
            val channel = NotificationChannel(channelId, channelName, importance).apply {
                description = "Betasan ihracat süreçleri ve cut-off hatırlatmaları"
                enableVibration(true)
                vibrationPattern = if (isUrgent) longArrayOf(0, 400, 200, 400) else longArrayOf(0, 200)
            }
            notificationManager.createNotificationChannel(channel)
        }

        // Tıklandığında uygulamayı aç
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("from_export_notification", true)
        }

        val pendingIntent = PendingIntent.getActivity(
            context,
            notifId,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val soundUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)

        val builder = NotificationCompat.Builder(context, channelId)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle(title)
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setPriority(if (isUrgent) NotificationCompat.PRIORITY_HIGH else NotificationCompat.PRIORITY_DEFAULT)
            .setSound(soundUri)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)

        notificationManager.notify(notifId, builder.build())
    }
}
