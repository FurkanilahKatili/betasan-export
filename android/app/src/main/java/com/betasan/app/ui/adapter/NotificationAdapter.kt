package com.betasan.app.ui.adapter

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.betasan.app.data.model.NotificationItem
import com.betasan.app.databinding.ItemNotificationCardBinding

class NotificationAdapter(
    private var notifications: List<NotificationItem> = emptyList(),
    private val onProductClick: (Int) -> Unit
) : RecyclerView.Adapter<NotificationAdapter.NotificationViewHolder>() {

    fun updateData(newList: List<NotificationItem>) {
        this.notifications = newList
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): NotificationViewHolder {
        val binding = ItemNotificationCardBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return NotificationViewHolder(binding)
    }

    override fun onBindViewHolder(holder: NotificationViewHolder, position: Int) {
        holder.bind(notifications[position])
    }

    override fun getItemCount(): Int = notifications.size

    inner class NotificationViewHolder(private val binding: ItemNotificationCardBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(item: NotificationItem) {
            binding.tvNotifTitle.text = item.title
            binding.tvNotifMessage.text = item.message
            binding.tvNotifDate.text = item.sent_at

            if (item.target_product_id != null && item.target_product_id > 0) {
                binding.btnViewProduct.visibility = View.VISIBLE
                binding.btnViewProduct.setOnClickListener {
                    onProductClick(item.target_product_id)
                }
            } else {
                binding.btnViewProduct.visibility = View.GONE
            }
        }
    }
}
