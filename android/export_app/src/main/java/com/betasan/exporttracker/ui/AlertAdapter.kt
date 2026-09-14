package com.betasan.exporttracker.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.betasan.exporttracker.data.ExportAlert
import com.betasan.exporttracker.databinding.ItemAlertCardBinding

class AlertAdapter(
    private var list: List<ExportAlert> = emptyList()
) : RecyclerView.Adapter<AlertAdapter.ViewHolder>() {

    fun updateList(newList: List<ExportAlert>) {
        list = newList
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemAlertCardBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(list[position])
    }

    override fun getItemCount() = list.size

    inner class ViewHolder(private val b: ItemAlertCardBinding) : RecyclerView.ViewHolder(b.root) {
        fun bind(item: ExportAlert) {
            b.tvAlertTitle.text = item.title
            b.tvAlertMessage.text = item.message
            b.tvAlertDate.text = item.createdAt ?: "Aktif Uyarı"
        }
    }
}
