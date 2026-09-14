package com.betasan.exporttracker.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.media.RingtoneManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.betasan.exporttracker.MainActivity
import com.betasan.exporttracker.data.ExportApiClient
import java.text.SimpleDateFormat
import java.util.Locale

class ExportStatusWorker(
    private val context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    companion object {
        const val CHANNEL_ID = "betasan_export_alerts_channel"
        const val CHANNEL_NAME = "İhracat & Cut-off Alarmları"
    }

    override suspend fun doWork(): Result {
        return try {
            val api = ExportApiClient.getApiService(context)

            try {
                api.checkAlerts()
            } catch (_: Exception) {}

            val response = api.getExports()
            if (response.isSuccessful && response.body()?.success == true) {
                val shipments = response.body()?.data ?: emptyList()
                var alertSent = false

                for (s in shipments) {
                    val cutoffStr = s.cutoffDatetime
                    if (!cutoffStr.isNullOrBlank()) {
                        val hoursLeft = calculateHoursLeft(cutoffStr)
                        val missingCount = s.totalTasks - s.doneTasks

                        if (hoursLeft in 0..48 && missingCount > 0) {
                            sendNotification(
                                id = s.id,
                                title = "🚨 Cut-off Uyarısı: ${s.fileNo} (${s.country})",
                                message = "${s.customerName} sevkiyatına $hoursLeft saat kaldı! Henüz $missingCount adet evrak tamamlanmadı."
                            )
                            alertSent = true
                        } else if (hoursLeft < 0 && missingCount > 0) {
                            sendNotification(
                                id = s.id,
                                title = "⛔ GECİKEN CUT-OFF: ${s.fileNo}",
                                message = "${s.customerName} için cut-off süresi doldu fakat $missingCount evrak eksik!"
                            )
                            alertSent = true
                        }
                    }
                }

                val isTest = inputData.getBoolean("is_test", false)
                if (isTest && !alertSent) {
                    sendNotification(
                        id = 9999,
                        title = "✅ Betasan İhracat Takip Aktif",
                        message = "Periyodik denetim başarıyla tamamlandı. Aktif ${shipments.size} sevkiyat kontrol edildi, kritik bir cut-off gecikmesi bulunmuyor."
                    )
                }
            }
            Result.success()
        } catch (e: Exception) {
            e.printStackTrace()
            Result.retry()
        }
    }

    private fun calculateHoursLeft(cutoffIso: String): Long {
        return try {
            val clean = cutoffIso.replace("T", " ")
            val format = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault())
            val cutoffDate = format.parse(clean) ?: return 999L
            val diffMs = cutoffDate.time - System.currentTimeMillis()
            diffMs / (1000 * 60 * 60)
        } catch (_: Exception) {
            999L
        }
    }

    private fun sendNotification(id: Int, title: String, message: String) {
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Acil cut-off tarihleri ve eksik ihracat evrakları bildirimleri"
                enableLights(true)
                lightColor = Color.RED
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 500, 200, 500)
            }
            notificationManager.createNotificationChannel(channel)
        }

        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("shipment_id", id)
        }

        val pendingIntent = PendingIntent.getActivity(
            context,
            id,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val soundUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle(title)
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setSound(soundUri)
            .setVibrate(longArrayOf(0, 500, 200, 500))
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        notificationManager.notify(id, notification)
    }
}
