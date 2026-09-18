package com.betasan.exporttracker.data

import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface ExportApiService {
    @GET("exports")
    suspend fun getExports(): Response<ExportListResponse>

    @GET("exports/{id}")
    suspend fun getExportDetail(@Path("id") id: Int): Response<ExportDetailResponse>

    @POST("exports/check_alerts")
    suspend fun checkAlerts(): Response<GenericResponse>

    @POST("exports/task/{id}/toggle")
    suspend fun toggleTask(@Path("id") id: Int): Response<TaskToggleResponse>

    @GET("customers")
    suspend fun getCustomers(): Response<CustomerListResponse>
}
