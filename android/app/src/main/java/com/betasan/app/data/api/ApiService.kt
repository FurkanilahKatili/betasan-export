package com.betasan.app.data.api

import com.betasan.app.data.model.*
import retrofit2.http.*

interface ApiService {

    @GET("get_products.php")
    suspend fun getProducts(
        @Query("category_id") categoryId: Int? = null,
        @Query("search") search: String? = null,
        @Query("only_discounted") onlyDiscounted: Int? = null,
        @Query("featured") featured: Int? = null
    ): ApiResponse<List<Product>>

    @GET("get_categories.php")
    suspend fun getCategories(): ApiResponse<List<Category>>

    @GET("get_banners.php")
    suspend fun getBanners(): ApiResponse<List<BannerItem>>

    @GET("get_product_detail.php")
    suspend fun getProductDetail(
        @Query("id") id: Int
    ): ApiResponse<Product>

    @GET("get_notifications.php")
    suspend fun getNotifications(): ApiResponse<List<NotificationItem>>

    @POST("register_device.php")
    suspend fun registerDevice(
        @Body body: Map<String, String>
    ): ApiResponse<Any>

    @POST("submit_inquiry.php")
    suspend fun submitInquiry(
        @Body request: SubmitInquiryRequest
    ): ApiResponse<SubmitInquiryResponse>

    // İhracat Takip & Durum Kontrol API'leri
    @GET("exports")
    suspend fun getExports(): ApiResponse<List<ExportShipmentItem>>

    @GET("exports/{id}")
    suspend fun getExportDetail(
        @Path("id") id: Int
    ): ExportDetailResponse

    @POST("exports/check_alerts")
    suspend fun checkExportAlerts(): ApiResponse<Any>
}
