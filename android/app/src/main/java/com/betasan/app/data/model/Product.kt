package com.betasan.app.data.model

import java.io.Serializable

data class Product(
    val id: Int,
    val name: String,
    val code: String? = null,
    val category_id: Int? = null,
    val category_name: String? = null,
    val description: String? = null,
    val image_url: String? = null,
    val discount_rate: Int = 0,
    val has_discount: Boolean = false,
    val is_featured: Boolean = false,
    val created_at: String? = null
) : Serializable
