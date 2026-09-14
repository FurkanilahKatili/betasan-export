package com.betasan.app.ui.cart

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.betasan.app.data.api.ApiClient
import com.betasan.app.data.cart.CartManager
import com.betasan.app.data.model.CartItem
import com.betasan.app.data.model.SubmitInquiryRequest
import com.betasan.app.databinding.ActivityCartBinding
import com.betasan.app.ui.adapter.CartAdapter
import kotlinx.coroutines.launch
import java.net.URLEncoder

class CartActivity : AppCompatActivity() {

    private lateinit var binding: ActivityCartBinding
    private lateinit var cartAdapter: CartAdapter
    private val cartManager by lazy { CartManager.getInstance(this) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCartBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupToolbar()
        setupRecyclerView()
        setupListeners()
        observeCart()
    }

    private fun setupToolbar() {
        binding.toolbarCart.setNavigationOnClickListener {
            finish()
        }

        binding.btnClearCart.setOnClickListener {
            showClearCartDialog()
        }
    }

    private fun setupRecyclerView() {
        cartAdapter = CartAdapter(
            onQuantityChange = { item, newQty ->
                cartManager.updateQuantity(item.product.id, newQty)
            },
            onDeleteClick = { item ->
                cartManager.removeFromCart(item.product.id)
                Toast.makeText(this, "${item.product.name} sepetten çıkarıldı.", Toast.LENGTH_SHORT).show()
            }
        )
        binding.rvCartItems.layoutManager = LinearLayoutManager(this)
        binding.rvCartItems.adapter = cartAdapter
    }

    private fun observeCart() {
        cartManager.cartItems.observe(this) { items ->
            if (items.isNullOrEmpty()) {
                binding.layoutCartContent.visibility = View.GONE
                binding.layoutEmptyCart.visibility = View.VISIBLE
                binding.btnClearCart.visibility = View.GONE
            } else {
                binding.layoutCartContent.visibility = View.VISIBLE
                binding.layoutEmptyCart.visibility = View.GONE
                binding.btnClearCart.visibility = View.VISIBLE

                cartAdapter.updateData(items)

                val totalCount = cartManager.getTotalCount()
                binding.tvTotalItemsTitle.text = "Talep Edilecek Ürünler ($totalCount Adet / ${items.size} Çeşit)"
            }
        }
    }

    private fun setupListeners() {
        binding.btnStartShopping.setOnClickListener {
            finish()
        }

        // WhatsApp ile Sipariş / Teklif Gönder
        binding.btnSendWhatsApp.setOnClickListener {
            sendOrderViaWhatsApp()
        }

        // E-Posta ile Gönder
        binding.btnSendEmail.setOnClickListener {
            sendOrderViaEmail()
        }
    }

    private fun sendOrderViaWhatsApp() {
        val items = cartManager.getItems()
        if (items.isEmpty()) {
            Toast.makeText(this, "Sepetiniz boş!", Toast.LENGTH_SHORT).show()
            return
        }

        val name = binding.etCustomerName.text.toString().trim()
        val phone = binding.etCustomerPhone.text.toString().trim()
        val notes = binding.etCustomerNotes.text.toString().trim()

        if (name.isBlank()) {
            binding.etCustomerName.error = "Lütfen adınızı veya kurum adınızı giriniz."
            binding.etCustomerName.requestFocus()
            return
        }

        val orderText = cartManager.formatOrderSummary(name, phone, notes)

        // cPanel Veritabanına da arka planda kaydet
        logInquiryToBackend(name, phone, notes, "whatsapp", orderText)

        // WhatsApp Yönlendirmesi
        try {
            val targetPhone = ApiClient.DEFAULT_WHATSAPP_NUMBER
            val encodedMessage = URLEncoder.encode(orderText, "UTF-8")
            val uri = Uri.parse("https://api.whatsapp.com/send?phone=$targetPhone&text=$encodedMessage")

            val intent = Intent(Intent.ACTION_VIEW, uri)
            startActivity(intent)
        } catch (e: Exception) {
            Toast.makeText(this, "WhatsApp uygulaması açılamadı: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun sendOrderViaEmail() {
        val items = cartManager.getItems()
        if (items.isEmpty()) {
            Toast.makeText(this, "Sepetiniz boş!", Toast.LENGTH_SHORT).show()
            return
        }

        val name = binding.etCustomerName.text.toString().trim()
        val phone = binding.etCustomerPhone.text.toString().trim()
        val notes = binding.etCustomerNotes.text.toString().trim()

        if (name.isBlank()) {
            binding.etCustomerName.error = "Lütfen adınızı veya kurum adınızı giriniz."
            binding.etCustomerName.requestFocus()
            return
        }

        val orderText = cartManager.formatOrderSummary(name, phone, notes)

        // cPanel Veritabanına kaydet
        logInquiryToBackend(name, phone, notes, "email", orderText)

        // E-Posta İstemcisini Aç
        try {
            val intent = Intent(Intent.ACTION_SENDTO).apply {
                data = Uri.parse("mailto:${ApiClient.DEFAULT_EMAIL_ADDRESS}")
                putExtra(Intent.EXTRA_SUBJECT, "Betasan Sipariş/Teklif Talebi - $name")
                putExtra(Intent.EXTRA_TEXT, orderText.replace("*", "")) // Mailde markdown yıldızlarını temizle
            }
            startActivity(Intent.createChooser(intent, "E-Posta Gönderici Seçin"))
        } catch (e: Exception) {
            Toast.makeText(this, "E-Posta uygulaması bulunamadı: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun logInquiryToBackend(name: String, phone: String, notes: String, channel: String, summary: String) {
        lifecycleScope.launch {
            try {
                ApiClient.service.submitInquiry(
                    SubmitInquiryRequest(
                        customer_name = name,
                        customer_phone = phone,
                        customer_notes = notes,
                        channel = channel,
                        items_summary = summary
                    )
                )
            } catch (e: Exception) {
                // Sessizce geç; WhatsApp/Mail açılması engellenmez
            }
        }
    }

    private fun showClearCartDialog() {
        AlertDialog.Builder(this)
            .setTitle("Sepeti Temizle")
            .setMessage("Sepetinizdeki tüm ürünler silinecek. Emin misiniz?")
            .setPositiveButton("Temizle") { _, _ ->
                cartManager.clearCart()
                Toast.makeText(this, "Sepet boşaltıldı.", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Vazgeç", null)
            .show()
    }
}
