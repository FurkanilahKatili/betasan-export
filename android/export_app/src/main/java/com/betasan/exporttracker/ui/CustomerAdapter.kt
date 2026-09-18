package com.betasan.exporttracker.ui

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.betasan.exporttracker.data.CustomerItem
import com.betasan.exporttracker.databinding.ItemCustomerCardBinding

class CustomerAdapter(
    private var list: List<CustomerItem> = emptyList(),
    private val onCallClick: (CustomerItem) -> Unit = {},
    private val onWhatsAppClick: (CustomerItem) -> Unit = {},
    private val onNewShipmentClick: (CustomerItem) -> Unit = {},
    private val onDeleteClick: (CustomerItem) -> Unit = {}
) : RecyclerView.Adapter<CustomerAdapter.ViewHolder>() {

    fun updateList(newList: List<CustomerItem>) {
        list = newList
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemCustomerCardBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(list[position])
    }

    override fun getItemCount() = list.size

    inner class ViewHolder(private val b: ItemCustomerCardBinding) : RecyclerView.ViewHolder(b.root) {
        fun bind(item: CustomerItem) {
            b.tvCompanyName.text = item.companyName

            val route = "📍 " + item.country + if (!item.destinationPort.isNullOrBlank()) " • " + item.destinationPort else ""
            b.tvCustomerRoute.text = route

            if (!item.contactInfo.isNullOrBlank()) {
                b.tvCustomerContact.visibility = View.VISIBLE
                b.tvCustomerContact.text = "👤 " + item.contactInfo
            } else {
                b.tvCustomerContact.visibility = View.GONE
            }

            if (!item.notes.isNullOrBlank()) {
                b.tvCustomerNotes.visibility = View.VISIBLE
                b.tvCustomerNotes.text = "📝 " + item.notes
            } else {
                b.tvCustomerNotes.visibility = View.GONE
            }

            b.btnCustomerCall.setOnClickListener { onCallClick(item) }
            b.btnCustomerWhatsApp.setOnClickListener { onWhatsAppClick(item) }
            b.btnCustomerNewShipment.setOnClickListener { onNewShipmentClick(item) }
            b.btnDeleteCustomer.setOnClickListener { onDeleteClick(item) }
        }
    }
}
