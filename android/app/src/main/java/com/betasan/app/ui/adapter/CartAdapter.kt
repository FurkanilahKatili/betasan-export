package com.betasan.app.ui.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.betasan.app.R
import com.betasan.app.data.model.CartItem
import com.betasan.app.databinding.ItemCartProductBinding
import com.bumptech.glide.Glide

class CartAdapter(
    private var cartItems: List<CartItem> = emptyList(),
    private val onQuantityChange: (CartItem, Int) -> Unit,
    private val onDeleteClick: (CartItem) -> Unit
) : RecyclerView.Adapter<CartAdapter.CartViewHolder>() {

    fun updateData(newItems: List<CartItem>) {
        this.cartItems = newItems
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): CartViewHolder {
        val binding = ItemCartProductBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return CartViewHolder(binding)
    }

    override fun onBindViewHolder(holder: CartViewHolder, position: Int) {
        holder.bind(cartItems[position])
    }

    override fun getItemCount(): Int = cartItems.size

    inner class CartViewHolder(private val binding: ItemCartProductBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(item: CartItem) {
            val product = item.product
            binding.tvCartItemName.text = product.name
            binding.tvCartItemCode.text = if (!product.code.isNullOrBlank()) "Kod: ${product.code}" else ""
            binding.tvQuantity.text = item.quantity.toString()

            Glide.with(binding.root.context)
                .load(product.image_url)
                .placeholder(R.drawable.bg_rounded_card)
                .error(R.drawable.bg_rounded_card)
                .into(binding.ivCartItem)

            binding.btnPlus.setOnClickListener {
                onQuantityChange(item, item.quantity + 1)
            }

            binding.btnMinus.setOnClickListener {
                if (item.quantity > 1) {
                    onQuantityChange(item, item.quantity - 1)
                } else {
                    onDeleteClick(item)
                }
            }

            binding.btnDelete.setOnClickListener {
                onDeleteClick(item)
            }
        }
    }
}
