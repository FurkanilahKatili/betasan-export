package com.betasan.exporttracker.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.betasan.exporttracker.R
import com.betasan.exporttracker.data.ShipmentItem
import com.betasan.exporttracker.databinding.ItemShipmentCardBinding
import java.text.SimpleDateFormat
import java.util.Locale

class ShipmentAdapter(
    private var list: List<ShipmentItem> = emptyList(),
    private val onItemClick: (ShipmentItem) -> Unit,
    private val onItemLongClick: ((ShipmentItem) -> Unit)? = null
) : RecyclerView.Adapter<ShipmentAdapter.ViewHolder>() {

    fun updateList(newList: List<ShipmentItem>) {
        list = newList
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemShipmentCardBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(list[position])
    }

    override fun getItemCount() = list.size

    inner class ViewHolder(private val b: ItemShipmentCardBinding) : RecyclerView.ViewHolder(b.root) {
        fun bind(item: ShipmentItem) {
            b.tvFileNo.text = item.fileNo
            b.tvCustomerName.text = item.customerName

            val route = "📍 " + item.country + (if (!item.destinationPort.isNullOrBlank()) " • " + item.destinationPort else "") + " (" + (item.incoterm ?: "FOB") + ")"
            b.tvRoute.text = route

            val carrierText = if (!item.carrierForwarder.isNullOrBlank()) "🚢 " + item.carrierForwarder else "Taşıyıcı: Belirtilmedi"
            b.tvCarrier.text = carrierText

            val hoursLeft = calculateHoursLeft(item.cutoffDatetime)
            if (hoursLeft < 0) {
                b.tvCutoffBadge.text = "⛔ Cut-off Geçti!"
                b.tvCutoffBadge.setBackgroundResource(R.drawable.bg_chip_urgent)
                b.tvCutoffBadge.setTextColor(ContextCompat.getColor(itemView.context, R.color.critical_red))
            } else if (hoursLeft <= 24) {
                b.tvCutoffBadge.text = "🚨 Son $hoursLeft Saat!"
                b.tvCutoffBadge.setBackgroundResource(R.drawable.bg_chip_urgent)
                b.tvCutoffBadge.setTextColor(ContextCompat.getColor(itemView.context, R.color.critical_red))
            } else if (hoursLeft <= 48) {
                b.tvCutoffBadge.text = "⏱️ Cut-off: $hoursLeft Saat"
                b.tvCutoffBadge.setBackgroundResource(R.drawable.bg_chip_warning)
                b.tvCutoffBadge.setTextColor(ContextCompat.getColor(itemView.context, R.color.accent_amber))
            } else {
                b.tvCutoffBadge.text = "✅ Güvenli: " + (hoursLeft / 24) + " Gün"
                b.tvCutoffBadge.setBackgroundResource(R.drawable.bg_chip_safe)
                b.tvCutoffBadge.setTextColor(ContextCompat.getColor(itemView.context, R.color.success_green))
            }

            b.tvTaskProgress.text = "${item.doneTasks}/${item.totalTasks} Evrak"
            if (item.totalTasks > 0) {
                val percent = (item.doneTasks * 100) / item.totalTasks
                b.pbTasks.progress = percent
            } else {
                b.pbTasks.progress = 0
            }

            itemView.setOnClickListener { onItemClick(item) }
            itemView.setOnLongClickListener {
                onItemLongClick?.invoke(item)
                true
            }
        }

        private fun calculateHoursLeft(cutoffIso: String?): Long {
            if (cutoffIso.isNullOrBlank()) return 999L
            return try {
                val clean = cutoffIso.replace("T", " ")
                val format = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault())
                val cutoffDate = format.parse(clean) ?: return 999L
                val diffMs = cutoffDate.time - System.currentTimeMillis()
                diffMs / (1000 * 60 * 60)
            } catch (_: Exception) {
                999L
            }
        }
    }
}
