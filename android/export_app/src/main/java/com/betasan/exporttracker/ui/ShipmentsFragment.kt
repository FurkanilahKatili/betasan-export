package com.betasan.exporttracker.ui

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.betasan.exporttracker.data.ExportApiClient
import com.betasan.exporttracker.databinding.FragmentShipmentsBinding
import kotlinx.coroutines.launch

class ShipmentsFragment : Fragment() {

    private var _binding: FragmentShipmentsBinding? = null
    private val binding get() = _binding!!
    private lateinit var adapter: ShipmentAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentShipmentsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = ShipmentAdapter { shipment ->
            val intent = Intent(requireContext(), ShipmentDetailActivity::class.java).apply {
                putExtra("shipment_id", shipment.id)
                putExtra("file_no", shipment.fileNo)
                putExtra("customer_name", shipment.customerName)
                putExtra("country", shipment.country)
                putExtra("port", shipment.destinationPort)
                putExtra("incoterm", shipment.incoterm)
                putExtra("cutoff", shipment.cutoffDatetime)
            }
            startActivity(intent)
        }

        binding.rvShipments.layoutManager = LinearLayoutManager(requireContext())
        binding.rvShipments.adapter = adapter

        binding.swipeRefresh.setOnRefreshListener {
            loadShipments()
        }

        loadShipments()
    }

    fun loadShipments() {
        binding.swipeRefresh.isRefreshing = true
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(requireContext())
                val response = api.getExports()
                if (response.isSuccessful && response.body()?.success == true) {
                    val list = response.body()?.data ?: emptyList()
                    adapter.updateList(list)
                    binding.tvEmptyState.visibility = if (list.isEmpty()) View.VISIBLE else View.GONE
                } else {
                    Toast.makeText(requireContext(), "Sevkiyatlar alınamadı", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Bağlantı hatası: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.swipeRefresh.isRefreshing = false
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
