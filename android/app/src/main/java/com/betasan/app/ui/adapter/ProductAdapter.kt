package com.betasan.app.ui.adapter

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.betasan.app.R
import com.betasan.app.data.model.Product
import com.betasan.app.databinding.ItemProductCardBinding
import com.bumptech.glide.Glide

class ProductAdapter(
    private var products: List<Product> = emptyList(),
    private val onProductClick: (Product) -> Unit,
    private val onAddToCartClick: (Product) -> Unit
) : RecyclerView.Adapter<ProductAdapter.ProductViewHolder>() {

    fun updateData(newProducts: List<Product>) {
        this.products = newProducts
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProductViewHolder {
        val binding = ItemProductCardBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ProductViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ProductViewHolder, position: Int) {
        holder.bind(products[position])
    }

    override fun getItemCount(): Int = products.size

    inner class ProductViewHolder(private val binding: ItemProductCardBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(product: Product) {
            binding.tvProductName.text = product.name

            if (!product.code.isNullOrBlank()) {
                binding.tvProductCode.text = "KOD: ${product.code}"
                binding.tvProductCode.visibility = View.VISIBLE
            } else {
                binding.tvProductCode.visibility = View.GONE
            }

            if (product.discount_rate > 0) {
                binding.tvDiscountBadge.text = "%${product.discount_rate} İndirim"
                binding.tvDiscountBadge.visibility = View.VISIBLE
            } else {
                binding.tvDiscountBadge.visibility = View.GONE
            }

            // Görsel yükleme (Glide)
            Glide.with(binding.root.context)
                .load(product.image_url)
                .placeholder(R.drawable.ic_product_placeholder)
                .error(R.drawable.ic_product_placeholder)
                .into(binding.ivProduct)

            binding.cardProduct.setOnClickListener {
                onProductClick(product)
            }

            binding.btnAddToCart.setOnClickListener {
                onAddToCartClick(product)
            }
        }
    }
}
