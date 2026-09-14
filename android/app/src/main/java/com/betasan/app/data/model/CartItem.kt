package com.betasan.app.data.model

import java.io.Serializable

data class CartItem(
    val product: Product,
    var quantity: Int = 1
) : Serializable
