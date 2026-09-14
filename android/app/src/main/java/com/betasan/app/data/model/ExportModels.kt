package com.betasan.app.data.model

import com.google.gson.annotations.SerializedName

data class ExportShipmentItem(
    @SerializedName("id") val id: Int,
    @SerializedName("file_no") val fileNo: String,
    @SerializedName("customer_name") val customerName: String,
    @SerializedName("country") val country: String,
    @SerializedName("destination_port") val destinationPort: String?,
    @SerializedName("incoterm") val incoterm: String?,
    @SerializedName("transport_mode") val transportMode: String?,
    @SerializedName("carrier_forwarder") val carrierForwarder: String?,
    @SerializedName("cutoff_datetime") val cutoffDatetime: String?,
    @SerializedName("etd") val etd: String?,
    @SerializedName("eta") val eta: String?,
    @SerializedName("status") val status: String,
    @SerializedName("total_tasks") val totalTasks: Int,
    @SerializedName("done_tasks") val doneTasks: Int,
    @SerializedName("has_alerts") val hasAlerts: Boolean,
    @SerializedName("alert_count") val alertCount: Int
)

data class ExportDetailResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("shipment") val shipment: ExportShipmentItem?,
    @SerializedName("tasks") val tasks: List<ExportTaskItem>?,
    @SerializedName("alerts") val alerts: List<ExportAlertItem>?
)

data class ExportTaskItem(
    @SerializedName("id") val id: Int,
    @SerializedName("title") val title: String,
    @SerializedName("category") val category: String?,
    @SerializedName("is_completed") val isCompleted: Int,
    @SerializedName("due_datetime") val dueDatetime: String?,
    @SerializedName("priority") val priority: String?,
    @SerializedName("tracking_code") val trackingCode: String?,
    @SerializedName("notes") val notes: String?
)

data class ExportAlertItem(
    @SerializedName("id") val id: Int,
    @SerializedName("alert_type") val alertType: String,
    @SerializedName("severity") val severity: String?,
    @SerializedName("title") val title: String,
    @SerializedName("message") val message: String
)
