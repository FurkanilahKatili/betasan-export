package com.betasan.exporttracker.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.betasan.exporttracker.R
import com.betasan.exporttracker.data.ExportTask
import com.betasan.exporttracker.databinding.ItemTaskChecklistBinding

class TaskAdapter(
    private var list: List<ExportTask> = emptyList(),
    private val onTaskToggle: (ExportTask) -> Unit = {}
) : RecyclerView.Adapter<TaskAdapter.ViewHolder>() {

    fun updateList(newList: List<ExportTask>) {
        list = newList
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemTaskChecklistBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(list[position])
    }

    override fun getItemCount() = list.size

    inner class ViewHolder(private val b: ItemTaskChecklistBinding) : RecyclerView.ViewHolder(b.root) {
        fun bind(item: ExportTask) {
            val ctx = b.root.context
            b.tvTaskTitle.text = item.title
            val isDone = item.isCompleted == 1

            val sub = when {
                !item.notes.isNullOrBlank() -> item.notes
                !item.dueDatetime.isNullOrBlank() -> "Son Tarih: ${item.dueDatetime}"
                isDone -> "Tamamlandı"
                item.priority == "urgent" -> "Öncelik: ACİL"
                else -> "Bekliyor"
            }
            b.tvTaskSubtitle.text = sub

            b.cbDelivered.setOnCheckedChangeListener(null)
            b.cbDelivered.isChecked = isDone

            if (isDone) {
                b.ivCheckStatus.setImageResource(R.drawable.ic_check_circle)
                b.tvDeliveredBadge.text = "EVET, İLETİLDİ ✓"
                b.tvDeliveredBadge.setTextColor(ContextCompat.getColor(ctx, R.color.success_green))
                b.tvDeliveredBadge.setBackgroundResource(R.drawable.bg_chip_safe)
            } else {
                b.ivCheckStatus.setImageResource(R.drawable.ic_pending)
                b.tvDeliveredBadge.text = "HAYIR (Bekliyor)"
                b.tvDeliveredBadge.setTextColor(ContextCompat.getColor(ctx, R.color.accent_amber))
                b.tvDeliveredBadge.setBackgroundResource(R.drawable.bg_chip_warning)
            }

            b.cbDelivered.setOnClickListener {
                onTaskToggle(item)
            }

            b.layoutCheckbox.setOnClickListener {
                b.cbDelivered.isChecked = !b.cbDelivered.isChecked
                onTaskToggle(item)
            }
        }
    }
}

