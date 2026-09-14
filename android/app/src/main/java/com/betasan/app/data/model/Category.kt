package com.betasan.app.data.model

data class Category(
    val id: Int,
    val name: String,
    val slug: String? = null,
    val icon: String? = null,
    val product_count: Int = 0
)
