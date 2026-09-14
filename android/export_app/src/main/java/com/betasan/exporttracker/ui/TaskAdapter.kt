package com.betasan.exporttracker.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.betasan.exporttracker.R
import com.betasan.exporttracker.data.ExportTask
import com.betasan.exporttracker.databinding.ItemTaskChecklistBinding

class TaskAdapter(
    private var list: List<ExportTask> = emptyList()
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
            b.tvTaskTitle.text = item.title
            val isDone = item.isCompleted == 1

            if (isDone) {
                b.ivCheckStatus.setImageResource(R.drawable.ic_check_circle)
                b.tvTaskSubtitle.text = "Durum: Tamamlandı ✓"
            } else {
                b.ivCheckStatus.setImageResource(R.drawable.ic_pending)
                val prio = when (item.priority) {
                    "high" -> "Yüksek Öncelik"
                    "urgent" -> "ACİL"
                    else -> "Normal"
                }
                b.tvTaskSubtitle.text = "Durum: Bekliyor • " + prio
            }
        }
    }
}
