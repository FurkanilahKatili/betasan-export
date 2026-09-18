package com.betasan.exporttracker.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.betasan.exporttracker.R
import com.betasan.exporttracker.data.AddTaskRequest
import com.betasan.exporttracker.data.ExportApiClient
import com.betasan.exporttracker.data.ExportTask
import com.betasan.exporttracker.databinding.ActivityShipmentDetailBinding
import com.betasan.exporttracker.databinding.DialogAddCustomTaskBinding
import kotlinx.coroutines.launch

class ShipmentDetailActivity : AppCompatActivity() {

    private lateinit var binding: ActivityShipmentDetailBinding
    private lateinit var taskAdapter: TaskAdapter
    private var shipmentId: Int = -1

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityShipmentDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)

        shipmentId = intent.getIntExtra("shipment_id", -1)
        val fileNo = intent.getStringExtra("file_no") ?: "EXP"
        val customer = intent.getStringExtra("customer_name") ?: "Müşteri"
        val country = intent.getStringExtra("country") ?: ""
        val port = intent.getStringExtra("port") ?: ""
        val incoterm = intent.getStringExtra("incoterm") ?: "FOB"
        val cutoff = intent.getStringExtra("cutoff") ?: ""

        binding.toolbarDetail.title = fileNo
        binding.toolbarDetail.setNavigationOnClickListener { finish() }

        binding.toolbarDetail.inflateMenu(R.menu.menu_shipment_detail)
        binding.toolbarDetail.setOnMenuItemClickListener { menuItem ->
            if (menuItem.itemId == R.id.action_delete_shipment) {
                confirmDeleteShipment()
                true
            } else {
                false
            }
        }

        binding.tvDetailFileNo.text = fileNo
        binding.tvDetailCustomer.text = customer
        binding.tvDetailRoute.text = "📍 $country • $port ($incoterm)"
        binding.tvDetailCutoff.text = "⏱️ Cut-off Tarihi: " + cutoff.replace("T", " ")

        taskAdapter = TaskAdapter(
            onTaskToggle = { task -> toggleTaskStatus(task) },
            onTaskDelete = { task -> confirmDeleteTask(task) }
        )
        binding.rvTasks.layoutManager = LinearLayoutManager(this)
        binding.rvTasks.adapter = taskAdapter

        binding.btnAddCustomTask.setOnClickListener {
            showAddCustomTaskDialog()
        }

        if (shipmentId != -1) {
            loadTasks()
        }
    }

    private fun showAddCustomTaskDialog() {
        val dialogBinding = DialogAddCustomTaskBinding.inflate(LayoutInflater.from(this))

        AlertDialog.Builder(this)
            .setView(dialogBinding.root)
            .setPositiveButton("Ekle") { _, _ ->
                val title = dialogBinding.etTaskTitle.text?.toString()?.trim() ?: ""
                val notes = dialogBinding.etTaskNotes.text?.toString()?.trim()
                val isUrgent = dialogBinding.cbIsUrgent.isChecked

                if (title.isBlank()) {
                    Toast.makeText(this, "Lütfen evrak veya ihtiyaç başlığı giriniz", Toast.LENGTH_SHORT).show()
                    return@setPositiveButton
                }

                addCustomTask(title, notes, if (isUrgent) "urgent" else "normal")
            }
            .setNegativeButton("İptal", null)
            .show()
    }

    private fun addCustomTask(title: String, notes: String?, priority: String) {
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(this@ShipmentDetailActivity)
                val req = AddTaskRequest(
                    title = title,
                    notes = notes,
                    priority = priority,
                    category = "custom"
                )
                val response = api.addCustomTask(shipmentId, req)
                if (response.isSuccessful && response.body()?.success == true) {
                    Toast.makeText(this@ShipmentDetailActivity, "Özel ihtiyaç / evrak eklendi", Toast.LENGTH_SHORT).show()
                    loadTasks()
                } else {
                    Toast.makeText(this@ShipmentDetailActivity, "İhtiyaç eklenemedi", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@ShipmentDetailActivity, "Hata: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun confirmDeleteTask(task: ExportTask) {
        AlertDialog.Builder(this)
            .setTitle("Görevi Sil")
            .setMessage("\"${task.title}\" ihtiyacını bu sevkiyattan kaldırmak istediğinize emin misiniz?")
            .setPositiveButton("Evet, Sil") { _, _ ->
                deleteTask(task)
            }
            .setNegativeButton("Vazgeç", null)
            .show()
    }

    private fun deleteTask(task: ExportTask) {
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(this@ShipmentDetailActivity)
                val response = api.deleteTask(task.id)
                if (response.isSuccessful && response.body()?.success == true) {
                    Toast.makeText(this@ShipmentDetailActivity, "Evrak listeden kaldırıldı", Toast.LENGTH_SHORT).show()
                    loadTasks()
                } else {
                    Toast.makeText(this@ShipmentDetailActivity, "Silinemedi", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@ShipmentDetailActivity, "Hata: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun confirmDeleteShipment() {
        AlertDialog.Builder(this)
            .setTitle("Sevkiyatı Sil")
            .setMessage("Bu sevkiyatı ve bağlı tüm evrak kayıtlarını kalıcı olarak silmek istediğinize emin misiniz?")
            .setPositiveButton("Evet, Tamamen Sil") { _, _ ->
                deleteShipment()
            }
            .setNegativeButton("Vazgeç", null)
            .show()
    }

    private fun deleteShipment() {
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(this@ShipmentDetailActivity)
                val response = api.deleteExport(shipmentId)
                if (response.isSuccessful && response.body()?.success == true) {
                    Toast.makeText(this@ShipmentDetailActivity, "Sevkiyat başarıyla silindi", Toast.LENGTH_SHORT).show()
                    finish()
                } else {
                    Toast.makeText(this@ShipmentDetailActivity, "Sevkiyat silinemedi", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@ShipmentDetailActivity, "Hata: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun toggleTaskStatus(task: ExportTask) {
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(this@ShipmentDetailActivity)
                val response = api.toggleTask(task.id)
                if (response.isSuccessful && response.body()?.success == true) {
                    val msg = response.body()?.message ?: "Evrak durumu güncellendi"
                    Toast.makeText(this@ShipmentDetailActivity, msg, Toast.LENGTH_SHORT).show()
                    loadTasks()
                } else {
                    Toast.makeText(this@ShipmentDetailActivity, "İşlem başarısız", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@ShipmentDetailActivity, "Hata: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun loadTasks() {
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(this@ShipmentDetailActivity)
                val response = api.getExportDetail(shipmentId)
                if (response.isSuccessful && response.body()?.success == true) {
                    val tasks = response.body()?.tasks ?: emptyList()
                    taskAdapter.updateList(tasks)
                }
            } catch (e: Exception) {
                Toast.makeText(this@ShipmentDetailActivity, "Evraklar yüklenemedi: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }
}
