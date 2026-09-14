package com.betasan.app.data.cart

import android.content.Context
import android.content.SharedPreferences
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import com.betasan.app.data.model.CartItem
import com.betasan.app.data.model.Product
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

class CartManager private constructor(context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences("betasan_cart_prefs", Context.MODE_PRIVATE)
    private val gson = Gson()
    private val _cartItems = MutableLiveData<List<CartItem>>(emptyList())
    val cartItems: LiveData<List<CartItem>> = _cartItems

    private val _cartCount = MutableLiveData<Int>(0)
    val cartCount: LiveData<Int> = _cartCount

    init {
        loadFromPrefs()
    }

    companion object {
        @Volatile
        private var INSTANCE: CartManager? = null

        fun getInstance(context: Context): CartManager {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: CartManager(context.applicationContext).also { INSTANCE = it }
            }
        }
    }

    private fun loadFromPrefs() {
        val json = prefs.getString("cart_items_json", null)
        if (!json.isNullOrEmpty()) {
            val type = object : TypeToken<MutableList<CartItem>>() {}.type
            val list: MutableList<CartItem> = try {
                gson.fromJson(json, type) ?: mutableListOf()
            } catch (e: Exception) {
                mutableListOf()
            }
            _cartItems.value = list
            updateCount(list)
        } else {
            _cartItems.value = emptyList()
            _cartCount.value = 0
        }
    }

    private fun saveToPrefs(list: List<CartItem>) {
        _cartItems.value = list
        updateCount(list)
        val json = gson.toJson(list)
        prefs.edit().putString("cart_items_json", json).apply()
    }

    private fun updateCount(list: List<CartItem>) {
        var count = 0
        for (item in list) {
            count += item.quantity
        }
        _cartCount.value = count
    }

    fun addToCart(product: Product, quantity: Int = 1) {
        val currentList = (_cartItems.value ?: emptyList()).toMutableList()
        val existingIndex = currentList.indexOfFirst { it.product.id == product.id }

        if (existingIndex >= 0) {
            val existing = currentList[existingIndex]
            currentList[existingIndex] = existing.copy(quantity = existing.quantity + quantity)
        } else {
            currentList.add(CartItem(product = product, quantity = quantity))
        }
        saveToPrefs(currentList)
    }

    fun updateQuantity(productId: Int, newQuantity: Int) {
        val currentList = (_cartItems.value ?: emptyList()).toMutableList()
        val existingIndex = currentList.indexOfFirst { it.product.id == productId }

        if (existingIndex >= 0) {
            if (newQuantity <= 0) {
                currentList.removeAt(existingIndex)
            } else {
                currentList[existingIndex] = currentList[existingIndex].copy(quantity = newQuantity)
            }
            saveToPrefs(currentList)
        }
    }

    fun removeFromCart(productId: Int) {
        val currentList = (_cartItems.value ?: emptyList()).toMutableList()
        val existingIndex = currentList.indexOfFirst { it.product.id == productId }
        if (existingIndex >= 0) {
            currentList.removeAt(existingIndex)
            saveToPrefs(currentList)
        }
    }

    fun clearCart() {
        saveToPrefs(emptyList())
    }

    fun getItems(): List<CartItem> {
        return _cartItems.value ?: emptyList()
    }

    fun getTotalCount(): Int {
        return _cartCount.value ?: 0
    }

    /**
     * WhatsApp ve E-Posta için hazır formatlı sipariş metni üretir.
     */
    fun formatOrderSummary(customerName: String, phone: String, notes: String): String {
        val sb = StringBuilder()
        sb.append("📋 *BETASAN MOBİL TEKLİF & SİPARİŞ TALEBİ*\n\n")

        sb.append("👤 *Müşteri / Kurum:* ").append(customerName.ifBlank { "Belirtilmedi" }).append("\n")
        if (phone.isNotBlank()) {
            sb.append("📞 *Telefon:* ").append(phone).append("\n")
        }
        sb.append("\n📦 *Talep Edilen Ürünler:*\n")

        val items = getItems()
        for ((index, item) in items.withIndex()) {
            val codeStr = if (!item.product.code.isNullOrBlank()) " [Kod: ${item.product.code}]" else ""
            val discountStr = if (item.product.discount_rate > 0) " (%${item.product.discount_rate} İndirimli)" else ""
            sb.append("${index + 1}. *${item.quantity} Adet* x ${item.product.name}$codeStr$discountStr\n")
        }

        if (notes.isNotBlank()) {
            sb.append("\n📝 *Müşteri Notu:* ").append(notes).append("\n")
        }

        sb.append("\n---\n*Betasan Mobil Uygulaması Üzerinden Oluşturulmuştur.*")
        return sb.toString()
    }
}
