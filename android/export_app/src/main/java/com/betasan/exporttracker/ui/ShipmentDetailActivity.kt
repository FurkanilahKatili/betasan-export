package com.betasan.exporttracker.ui

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.betasan.exporttracker.data.ExportApiClient
import com.betasan.exporttracker.data.ExportTask
import com.betasan.exporttracker.databinding.ActivityShipmentDetailBinding
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

        binding.tvDetailFileNo.text = fileNo
        binding.tvDetailCustomer.text = customer
        binding.tvDetailRoute.text = "📍 $country • $port ($incoterm)"
        binding.tvDetailCutoff.text = "⏱️ Cut-off Tarihi: " + cutoff.replace("T", " ")

        taskAdapter = TaskAdapter { task ->
            toggleTaskStatus(task)
        }
        binding.rvTasks.layoutManager = LinearLayoutManager(this)
        binding.rvTasks.adapter = taskAdapter

        if (shipmentId != -1) {
            loadTasks()
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
