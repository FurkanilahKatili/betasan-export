package com.betasan.exporttracker.data

import com.google.gson.annotations.SerializedName

data class ExportListResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("data") val data: List<ShipmentItem>?
)

data class ExportDetailResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("shipment") val shipment: ShipmentItem?,
    @SerializedName("tasks") val tasks: List<ExportTask>?,
    @SerializedName("alerts") val alerts: List<ExportAlert>?
)

data class ShipmentItem(
    @SerializedName("id") val id: Int,
    @SerializedName("file_no") val fileNo: String,
    @SerializedName("customer_name") val customerName: String,
    @SerializedName("country") val country: String,
    @SerializedName("destination_port") val destinationPort: String?,
    @SerializedName("incoterm") val incoterm: String?,
    @SerializedName("transport_mode") val transportMode: String?,
    @SerializedName("carrier_forwarder") val carrierForwarder: String?,
    @SerializedName("loading_date") val loadingDate: String?,
    @SerializedName("cutoff_datetime") val cutoffDatetime: String?,
    @SerializedName("etd") val etd: String?,
    @SerializedName("eta") val eta: String?,
    @SerializedName("status") val status: String?,
    @SerializedName("notes") val notes: String?,
    @SerializedName("total_tasks") val totalTasks: Int = 0,
    @SerializedName("done_tasks") val doneTasks: Int = 0,
    @SerializedName("has_alerts") val hasAlerts: Boolean = false,
    @SerializedName("alert_count") val alertCount: Int = 0
)

data class ExportTask(
    @SerializedName("id") val id: Int,
    @SerializedName("shipment_id") val shipmentId: Int,
    @SerializedName("title") val title: String,
    @SerializedName("category") val category: String?,
    @SerializedName("is_completed") val isCompleted: Int,
    @SerializedName("completed_at") val completedAt: String?,
    @SerializedName("due_datetime") val dueDatetime: String?,
    @SerializedName("document_file_url") val documentFileUrl: String?,
    @SerializedName("tracking_code") val trackingCode: String?,
    @SerializedName("notes") val notes: String?,
    @SerializedName("priority") val priority: String?
)

data class ExportAlert(
    @SerializedName("id") val id: Int,
    @SerializedName("shipment_id") val shipmentId: Int,
    @SerializedName("task_id") val taskId: Int?,
    @SerializedName("alert_type") val alertType: String,
    @SerializedName("severity") val severity: String?,
    @SerializedName("title") val title: String,
    @SerializedName("message") val message: String,
    @SerializedName("is_resolved") val isResolved: Int,
    @SerializedName("created_at") val createdAt: String?
)

data class GenericResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String?
)

data class TaskToggleResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("task_id") val taskId: Int?,
    @SerializedName("is_completed") val isCompleted: Int?,
    @SerializedName("completed_at") val completedAt: String?,
    @SerializedName("message") val message: String?
)

data class CustomerListResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("customers") val customers: List<CustomerItem>?,
    @SerializedName("count") val count: Int = 0
)

data class CustomerItem(
    @SerializedName("id") val id: Int,
    @SerializedName("company_name") val companyName: String,
    @SerializedName("country") val country: String,
    @SerializedName("destination_port") val destinationPort: String?,
    @SerializedName("contact_info") val contactInfo: String?,
    @SerializedName("notes") val notes: String?
)

data class CreateShipmentRequest(
    @SerializedName("file_no") val fileNo: String,
    @SerializedName("customer_name") val customerName: String,
    @SerializedName("country") val country: String,
    @SerializedName("destination_port") val destinationPort: String? = null,
    @SerializedName("transport_mode") val transportMode: String = "sea",
    @SerializedName("incoterm") val incoterm: String = "FOB",
    @SerializedName("carrier_forwarder") val carrierForwarder: String? = null,
    @SerializedName("notes") val notes: String? = null,
    @SerializedName("custom_tasks") val customTasks: List<String> = emptyList()
)

data class AddTaskRequest(
    @SerializedName("title") val title: String,
    @SerializedName("notes") val notes: String? = null,
    @SerializedName("priority") val priority: String = "normal",
    @SerializedName("category") val category: String = "custom"
)


