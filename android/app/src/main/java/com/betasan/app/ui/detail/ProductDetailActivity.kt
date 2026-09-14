package com.betasan.app.ui.detail

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.betasan.app.R
import com.betasan.app.data.api.ApiClient
import com.betasan.app.data.cart.CartManager
import com.betasan.app.data.model.Product
import com.betasan.app.databinding.ActivityProductDetailBinding
import com.betasan.app.ui.cart.CartActivity
import com.bumptech.glide.Glide
import kotlinx.coroutines.launch
import java.net.URLEncoder

class ProductDetailActivity : AppCompatActivity() {

    private lateinit var binding: ActivityProductDetailBinding
    private var product: Product? = null
    private var quantity: Int = 1

    companion object {
        const val EXTRA_PRODUCT = "extra_product"
        const val EXTRA_PRODUCT_ID = "extra_product_id"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProductDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupToolbar()
        observeCart()

        product = intent.getSerializableExtra(EXTRA_PRODUCT) as? Product
        val productId = intent.getIntExtra(EXTRA_PRODUCT_ID, 0)

        if (product != null) {
            bindProduct(product!!)
        } else if (productId > 0) {
            loadProductById(productId)
        } else {
            Toast.makeText(this, "Ürün bilgisi yüklenemedi.", Toast.LENGTH_SHORT).show()
            finish()
        }

        setupQuantityControls()
        setupActions()
    }

    private fun setupToolbar() {
        binding.toolbarDetail.setNavigationOnClickListener {
            finish()
        }

        binding.btnCartDetailHeader.setOnClickListener {
            startActivity(Intent(this, CartActivity::class.java))
        }
    }

    private fun observeCart() {
        CartManager.getInstance(this).cartCount.observe(this) { count ->
            if (count > 0) {
                binding.tvCartBadgeDetail.text = count.toString()
                binding.tvCartBadgeDetail.visibility = View.VISIBLE
            } else {
                binding.tvCartBadgeDetail.visibility = View.GONE
            }
        }
    }

    private fun loadProductById(id: Int) {
        lifecycleScope.launch {
            try {
                val res = ApiClient.service.getProductDetail(id)
                if (res.success && res.data != null) {
                    product = res.data
                    bindProduct(res.data)
                } else {
                    fallbackMock(id)
                }
            } catch (e: Exception) {
                fallbackMock(id)
            }
        }
    }

    private fun fallbackMock(id: Int) {
        val found = com.betasan.app.data.MockDataProvider.getProducts().find { it.id == id }
        if (found != null) {
            product = found
            bindProduct(found)
        } else {
            Toast.makeText(this@ProductDetailActivity, "Ürün bulunamadı.", Toast.LENGTH_SHORT).show()
            finish()
        }
    }

    private fun bindProduct(p: Product) {
        binding.tvDetailName.text = p.name
        binding.tvDetailCategory.text = p.category_name ?: "Medikal Ürün"

        if (!p.code.isNullOrBlank()) {
            binding.tvDetailCode.text = "KOD: ${p.code}"
            binding.tvDetailCode.visibility = View.VISIBLE
        } else {
            binding.tvDetailCode.visibility = View.GONE
        }

        if (p.discount_rate > 0) {
            binding.tvDetailDiscountBadge.text = "%${p.discount_rate} İndirim"
            binding.tvDetailDiscountBadge.visibility = View.VISIBLE
        } else {
            binding.tvDetailDiscountBadge.visibility = View.GONE
        }

        binding.tvDetailDescription.text = if (!p.description.isNullOrBlank()) {
            p.description
        } else {
            "Bu ürün için detaylı açıklama girilmemiştir."
        }

        Glide.with(this)
            .load(p.image_url)
            .placeholder(R.drawable.bg_rounded_card)
            .error(R.drawable.bg_rounded_card)
            .into(binding.ivDetailImage)
    }

    private fun setupQuantityControls() {
        binding.btnDetailMinus.setOnClickListener {
            if (quantity > 1) {
                quantity--
                binding.tvDetailQuantity.text = quantity.toString()
            }
        }

        binding.btnDetailPlus.setOnClickListener {
            quantity++
            binding.tvDetailQuantity.text = quantity.toString()
        }
    }

    private fun setupActions() {
        // Sepete Ekle
        binding.btnDetailAddToCart.setOnClickListener {
            product?.let { p ->
                CartManager.getInstance(this).addToCart(p, quantity)
                Toast.makeText(this, "$quantity Adet ${p.name} sepete eklendi!", Toast.LENGTH_SHORT).show()
            }
        }

        // Hızlı WhatsApp Bilgi Alma
        binding.btnDetailQuickWhatsApp.setOnClickListener {
            product?.let { p ->
                openQuickWhatsAppInquiry(p)
            }
        }
    }

    private fun openQuickWhatsAppInquiry(p: Product) {
        try {
            val phone = ApiClient.DEFAULT_WHATSAPP_NUMBER
            val codeStr = if (!p.code.isNullOrBlank()) " (Kod: ${p.code})" else ""
            val message = "Merhaba Betasan, mobil uygulamanızda yer alan *${p.name}*$codeStr ürünü hakkında detaylı bilgi ve fiyat teklifi almak istiyorum."
            val url = "https://api.whatsapp.com/send?phone=$phone&text=${URLEncoder.encode(message, "UTF-8")}"

            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            startActivity(intent)
        } catch (e: Exception) {
            Toast.makeText(this, "WhatsApp uygulaması açılamadı: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }
}
