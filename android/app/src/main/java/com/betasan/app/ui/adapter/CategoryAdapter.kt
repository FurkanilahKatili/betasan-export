package com.betasan.app.ui.adapter

import android.graphics.Color
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.betasan.app.R
import com.betasan.app.data.model.Category
import com.betasan.app.databinding.ItemCategoryChipBinding

class CategoryAdapter(
    private var categories: List<Category> = emptyList(),
    private var selectedCategoryId: Int? = null,
    private val onCategorySelected: (Category?) -> Unit
) : RecyclerView.Adapter<CategoryAdapter.CategoryViewHolder>() {

    fun updateData(newCategories: List<Category>, selectedId: Int? = null) {
        this.categories = newCategories
        this.selectedCategoryId = selectedId
        notifyDataSetChanged()
    }

    fun setSelectedCategory(categoryId: Int?) {
        this.selectedCategoryId = categoryId
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): CategoryViewHolder {
        val binding = ItemCategoryChipBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return CategoryViewHolder(binding)
    }

    override fun onBindViewHolder(holder: CategoryViewHolder, position: Int) {
        val category = categories[position]
        holder.bind(category, category.id == selectedCategoryId)
    }

    override fun getItemCount(): Int = categories.size

    inner class CategoryViewHolder(private val binding: ItemCategoryChipBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(category: Category, isSelected: Boolean) {
            val countStr = if (category.product_count > 0) " (${category.product_count})" else ""
            binding.tvCategoryName.text = "${category.name}$countStr"

            val context = binding.root.context
            if (isSelected) {
                binding.chipContainer.backgroundTintList = ContextCompat.getColorStateList(context, R.color.primary)
                binding.tvCategoryName.setTextColor(Color.WHITE)
            } else {
                binding.chipContainer.backgroundTintList = ContextCompat.getColorStateList(context, R.color.surface)
                binding.tvCategoryName.setTextColor(ContextCompat.getColor(context, R.color.text_primary))
            }

            binding.root.setOnClickListener {
                selectedCategoryId = if (selectedCategoryId == category.id) null else category.id
                notifyDataSetChanged()
                onCategorySelected(if (selectedCategoryId == category.id) category else null)
            }
        }
    }
}
