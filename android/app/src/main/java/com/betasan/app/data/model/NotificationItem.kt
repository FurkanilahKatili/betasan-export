package com.betasan.app.data.model

data class NotificationItem(
    val id: Int,
    val title: String,
    val message: String,
    val target_product_id: Int? = null,
    val product_name: String? = null,
    val product_image_url: String? = null,
    val sent_at: String
)
