package com.betasan.exporttracker.ui

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.betasan.exporttracker.data.CreateShipmentRequest
import com.betasan.exporttracker.data.CustomerItem
import com.betasan.exporttracker.data.ExportApiClient
import com.betasan.exporttracker.data.ShipmentItem
import com.betasan.exporttracker.databinding.DialogAddShipmentBinding
import com.betasan.exporttracker.databinding.FragmentShipmentsBinding
import kotlinx.coroutines.launch

class ShipmentsFragment : Fragment() {

    private var _binding: FragmentShipmentsBinding? = null
    private val binding get() = _binding!!
    private lateinit var adapter: ShipmentAdapter
    private var customerList: List<CustomerItem> = emptyList()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentShipmentsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = ShipmentAdapter(
            onItemClick = { shipment ->
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
            },
            onItemLongClick = { shipment ->
                confirmDeleteShipment(shipment)
            }
        )

        binding.rvShipments.layoutManager = LinearLayoutManager(requireContext())
        binding.rvShipments.adapter = adapter

        binding.swipeRefresh.setOnRefreshListener {
            loadShipments()
        }

        binding.fabAddShipment.setOnClickListener {
            showAddShipmentDialog()
        }

        loadShipments()
    }

    override fun onResume() {
        super.onResume()
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

    private fun confirmDeleteShipment(shipment: ShipmentItem) {
        AlertDialog.Builder(requireContext())
            .setTitle("Sevkiyatı Sil")
            .setMessage("\"${shipment.fileNo} - ${shipment.customerName}\" siparişini silmek istediğinize emin misiniz?")
            .setPositiveButton("Evet, Sil") { _, _ ->
                deleteShipment(shipment.id)
            }
            .setNegativeButton("Vazgeç", null)
            .show()
    }

    private fun deleteShipment(id: Int) {
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(requireContext())
                val response = api.deleteExport(id)
                if (response.isSuccessful && response.body()?.success == true) {
                    Toast.makeText(requireContext(), "Sevkiyat silindi", Toast.LENGTH_SHORT).show()
                    loadShipments()
                } else {
                    Toast.makeText(requireContext(), "Silme işlemi başarısız", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Hata: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun showAddShipmentDialog() {
        val dialogBinding = DialogAddShipmentBinding.inflate(LayoutInflater.from(requireContext()))

        // Fetch customers to populate autocomplete
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(requireContext())
                val custRes = api.getCustomers()
                if (custRes.isSuccessful && custRes.body()?.success == true) {
                    customerList = custRes.body()?.customers ?: emptyList()
                    val names = customerList.map { it.companyName }
                    val autoAdapter = ArrayAdapter(requireContext(), android.R.layout.simple_dropdown_item_1line, names)
                    dialogBinding.actvCustomerName.setAdapter(autoAdapter)

                    dialogBinding.actvCustomerName.setOnItemClickListener { _, _, position, _ ->
                        val selectedName = autoAdapter.getItem(position)
                        val match = customerList.find { it.companyName.equals(selectedName, ignoreCase = true) }
                        if (match != null) {
                            if (!match.country.isNullOrBlank()) {
                                dialogBinding.etCountry.setText(match.country)
                            }
                            if (!match.destinationPort.isNullOrBlank()) {
                                dialogBinding.etPort.setText(match.destinationPort)
                            }
                        }
                    }
                }
            } catch (_: Exception) {
                // Ignore if customer list fetch fails
            }
        }

        AlertDialog.Builder(requireContext())
            .setView(dialogBinding.root)
            .setPositiveButton("Siparişi Kaydet") { _, _ ->
                val customerName = dialogBinding.actvCustomerName.text?.toString()?.trim() ?: ""
                val fileNo = dialogBinding.etFileNo.text?.toString()?.trim() ?: ""
                val country = dialogBinding.etCountry.text?.toString()?.trim() ?: ""
                val port = dialogBinding.etPort.text?.toString()?.trim()
                val carrier = dialogBinding.etCarrier.text?.toString()?.trim()
                val notes = dialogBinding.etNotes.text?.toString()?.trim()

                if (customerName.isBlank()) {
                    Toast.makeText(requireContext(), "Müşteri adı zorunludur", Toast.LENGTH_SHORT).show()
                    return@setPositiveButton
                }

                if (country.isBlank()) {
                    Toast.makeText(requireContext(), "Hedef ülke zorunludur", Toast.LENGTH_SHORT).show()
                    return@setPositiveButton
                }

                val finalFileNo = if (fileNo.isBlank()) "EXP-${System.currentTimeMillis() % 10000}" else fileNo

                val req = CreateShipmentRequest(
                    fileNo = finalFileNo,
                    customerName = customerName,
                    country = country,
                    destinationPort = if (port.isNullOrBlank()) null else port,
                    carrierForwarder = if (carrier.isNullOrBlank()) null else carrier,
                    notes = if (notes.isNullOrBlank()) null else notes
                )

                createShipment(req)
            }
            .setNegativeButton("İptal", null)
            .show()
    }

    private fun createShipment(req: CreateShipmentRequest) {
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(requireContext())
                val response = api.createExport(req)
                if (response.isSuccessful && response.body()?.success == true) {
                    Toast.makeText(requireContext(), "Yeni sipariş başarıyla oluşturuldu", Toast.LENGTH_SHORT).show()
                    loadShipments()
                } else {
                    Toast.makeText(requireContext(), "Sipariş oluşturulamadı", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Hata: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
