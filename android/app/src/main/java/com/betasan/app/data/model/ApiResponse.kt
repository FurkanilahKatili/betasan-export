package com.betasan.app.data.model

data class ApiResponse<T>(
    val success: Boolean,
    val message: String?,
    val data: T?
)

data class SubmitInquiryRequest(
    val customer_name: String,
    val customer_phone: String,
    val customer_notes: String,
    val channel: String,
    val items_summary: String
)

data class SubmitInquiryResponse(
    val order_id: Int,
    val whatsapp_number: String?,
    val email_address: String?
)
