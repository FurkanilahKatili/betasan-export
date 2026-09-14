package com.betasan.app.data.model

data class BannerItem(
    val id: Int,
    val title: String,
    val subtitle: String? = null,
    val badge: String? = null,
    val product_id: Int? = null,
    val image_url: String? = null
)
