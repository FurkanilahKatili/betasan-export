package com.betasan.exporttracker.ui

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.betasan.exporttracker.data.CreateCustomerRequest
import com.betasan.exporttracker.data.CreateShipmentRequest
import com.betasan.exporttracker.data.CustomerItem
import com.betasan.exporttracker.data.ExportApiClient
import com.betasan.exporttracker.databinding.DialogAddCustomerBinding
import com.betasan.exporttracker.databinding.DialogAddShipmentBinding
import com.betasan.exporttracker.databinding.FragmentCustomersBinding
import kotlinx.coroutines.launch

class CustomersFragment : Fragment() {

    private var _binding: FragmentCustomersBinding? = null
    private val binding get() = _binding!!
    private lateinit var adapter: CustomerAdapter
    private var customerList: List<CustomerItem> = emptyList()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentCustomersBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = CustomerAdapter(
            onCallClick = { customer -> dialCustomer(customer) },
            onWhatsAppClick = { customer -> openWhatsAppCustomer(customer) },
            onNewShipmentClick = { customer -> openNewShipmentForCustomer(customer) },
            onDeleteClick = { customer -> confirmDeleteCustomer(customer) }
        )

        binding.rvCustomers.layoutManager = LinearLayoutManager(requireContext())
        binding.rvCustomers.adapter = adapter

        binding.swipeRefreshCustomers.setOnRefreshListener {
            loadCustomers()
        }

        binding.fabAddCustomer.setOnClickListener {
            showAddCustomerDialog()
        }

        loadCustomers()
    }

    override fun onResume() {
        super.onResume()
        loadCustomers()
    }

    fun loadCustomers() {
        binding.swipeRefreshCustomers.isRefreshing = true
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(requireContext())
                val response = api.getCustomers()
                if (response.isSuccessful && response.body()?.success == true) {
                    customerList = response.body()?.customers ?: emptyList()
                    adapter.updateList(customerList)
                    binding.tvCustomerEmptyState.visibility = if (customerList.isEmpty()) View.VISIBLE else View.GONE
                } else {
                    Toast.makeText(requireContext(), "Müşteriler alınamadı", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Bağlantı hatası: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.swipeRefreshCustomers.isRefreshing = false
            }
        }
    }

    private fun extractPhone(contactInfo: String?): String? {
        if (contactInfo.isNullOrBlank()) return null
        val digits = contactInfo.filter { it.isDigit() || it == '+' }
        return if (digits.length >= 7) digits else null
    }

    private fun dialCustomer(customer: CustomerItem) {
        val phone = extractPhone(customer.contactInfo)
        if (phone.isNullOrBlank()) {
            Toast.makeText(requireContext(), "Müşteri için kayıtlı telefon numarası bulunamadı", Toast.LENGTH_SHORT).show()
            return
        }
        try {
            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$phone"))
            startActivity(intent)
        } catch (e: Exception) {
            Toast.makeText(requireContext(), "Arama başlatılamadı: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun openWhatsAppCustomer(customer: CustomerItem) {
        val phone = extractPhone(customer.contactInfo)
        if (phone.isNullOrBlank()) {
            Toast.makeText(requireContext(), "Müşteri için kayıtlı telefon numarası bulunamadı", Toast.LENGTH_SHORT).show()
            return
        }
        val cleanDigits = phone.replace("+", "").trim()
        val text = "Merhaba Sayın Yetkili, Betasan İhracat Departmanı olarak sizinle iletişime geçiyoruz."
        val url = "https://api.whatsapp.com/send?phone=$cleanDigits&text=" + Uri.encode(text)
        try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            startActivity(intent)
        } catch (e: Exception) {
            Toast.makeText(requireContext(), "WhatsApp açılamadı: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun openNewShipmentForCustomer(customer: CustomerItem) {
        val dialogBinding = DialogAddShipmentBinding.inflate(LayoutInflater.from(requireContext()))

        dialogBinding.actvCustomerName.setText(customer.companyName)
        if (!customer.country.isNullOrBlank()) {
            dialogBinding.etCountry.setText(customer.country)
        }
        if (!customer.destinationPort.isNullOrBlank()) {
            dialogBinding.etPort.setText(customer.destinationPort)
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
                } else {
                    Toast.makeText(requireContext(), "Sipariş oluşturulamadı", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Hata: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun showAddCustomerDialog() {
        val dialogBinding = DialogAddCustomerBinding.inflate(LayoutInflater.from(requireContext()))

        AlertDialog.Builder(requireContext())
            .setView(dialogBinding.root)
            .setPositiveButton("Müşteriyi Kaydet") { _, _ ->
                val companyName = dialogBinding.etCustomerCompanyName.text?.toString()?.trim() ?: ""
                val country = dialogBinding.etCustomerCountry.text?.toString()?.trim() ?: ""
                val port = dialogBinding.etCustomerPort.text?.toString()?.trim()
                val contact = dialogBinding.etCustomerContact.text?.toString()?.trim()
                val notes = dialogBinding.etCustomerNotes.text?.toString()?.trim()

                if (companyName.isBlank()) {
                    Toast.makeText(requireContext(), "Firma adı zorunludur", Toast.LENGTH_SHORT).show()
                    return@setPositiveButton
                }
                if (country.isBlank()) {
                    Toast.makeText(requireContext(), "Ülke zorunludur", Toast.LENGTH_SHORT).show()
                    return@setPositiveButton
                }

                val req = CreateCustomerRequest(
                    companyName = companyName,
                    country = country,
                    destinationPort = if (port.isNullOrBlank()) null else port,
                    contactInfo = if (contact.isNullOrBlank()) null else contact,
                    notes = if (notes.isNullOrBlank()) null else notes
                )

                addCustomer(req)
            }
            .setNegativeButton("İptal", null)
            .show()
    }

    private fun addCustomer(req: CreateCustomerRequest) {
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(requireContext())
                val response = api.addCustomer(req)
                if (response.isSuccessful && response.body()?.success == true) {
                    Toast.makeText(requireContext(), "Müşteri rehbere eklendi", Toast.LENGTH_SHORT).show()
                    loadCustomers()
                } else {
                    Toast.makeText(requireContext(), "Müşteri eklenemedi", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Hata: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun confirmDeleteCustomer(customer: CustomerItem) {
        AlertDialog.Builder(requireContext())
            .setTitle("Müşteriyi Sil")
            .setMessage("\"${customer.companyName}\" müşterisini rehberden silmek istediğinize emin misiniz?")
            .setPositiveButton("Evet, Sil") { _, _ ->
                deleteCustomer(customer.id)
            }
            .setNegativeButton("Vazgeç", null)
            .show()
    }

    private fun deleteCustomer(id: Int) {
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(requireContext())
                val response = api.deleteCustomer(id)
                if (response.isSuccessful && response.body()?.success == true) {
                    Toast.makeText(requireContext(), "Müşteri silindi", Toast.LENGTH_SHORT).show()
                    loadCustomers()
                } else {
                    Toast.makeText(requireContext(), "Silinemedi", Toast.LENGTH_SHORT).show()
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
