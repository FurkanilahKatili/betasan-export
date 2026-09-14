package com.betasan.app.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.betasan.app.MainActivity
import com.betasan.app.R
import com.betasan.app.data.api.ApiClient
import com.betasan.app.ui.detail.ProductDetailActivity
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class BetasanFirebaseService : FirebaseMessagingService() {

    companion object {
        private const val CHANNEL_ID = "betasan_campaigns"
        private const val CHANNEL_NAME = "Betasan Kampanyalar ve İndirimler"
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        CoroutineScope(Dispatchers.IO).launch {
            try {
                ApiClient.service.registerDevice(
                    mapOf("token" to token, "device_type" to "android")
                )
            } catch (e: Exception) {
                // Ignore
            }
        }
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)

        val title = remoteMessage.notification?.title 
            ?: remoteMessage.data["title"] 
            ?: "Betasan Kampanya Duyurusu"

        val body = remoteMessage.notification?.body 
            ?: remoteMessage.data["body"] 
            ?: "Yeni bir indirim fırsatını inceleyin!"

        val productIdStr = remoteMessage.data["product_id"]
        val productId = productIdStr?.toIntOrNull()

        showSystemNotification(title, body, productId)
    }

    private fun showSystemNotification(title: String, body: String, productId: Int?) {
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        // Android 8.0+ için bildirim kanalı oluştur
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Betasan indirim ve kampanya anlık bildirimleri"
            }
            notificationManager.createNotificationChannel(channel)
        }

        val intent = if (productId != null && productId > 0) {
            Intent(this, ProductDetailActivity::class.java).apply {
                putExtra(ProductDetailActivity.EXTRA_PRODUCT_ID, productId)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
        } else {
            Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            System.currentTimeMillis().toInt(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notifications)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        notificationManager.notify(System.currentTimeMillis().toInt(), notification)
    }
}
