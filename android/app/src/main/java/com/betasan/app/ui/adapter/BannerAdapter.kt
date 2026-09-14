package com.betasan.app.ui.adapter

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.betasan.app.R
import com.betasan.app.data.model.BannerItem
import com.betasan.app.databinding.ItemBannerBinding
import com.bumptech.glide.Glide

class BannerAdapter(
    private var banners: List<BannerItem> = emptyList(),
    private val onBannerClick: (BannerItem) -> Unit
) : RecyclerView.Adapter<BannerAdapter.BannerViewHolder>() {

    fun updateData(newBanners: List<BannerItem>) {
        this.banners = newBanners
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): BannerViewHolder {
        val binding = ItemBannerBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return BannerViewHolder(binding)
    }

    override fun onBindViewHolder(holder: BannerViewHolder, position: Int) {
        holder.bind(banners[position])
    }

    override fun getItemCount(): Int = banners.size

    inner class BannerViewHolder(private val binding: ItemBannerBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(banner: BannerItem) {
            binding.tvBannerTitle.text = banner.title
            binding.tvBannerSubtitle.text = banner.subtitle ?: "Betasan Medikal Ürünleri"

            if (!banner.badge.isNullOrBlank()) {
                binding.tvBannerBadge.text = banner.badge
                binding.tvBannerBadge.visibility = View.VISIBLE
            } else {
                binding.tvBannerBadge.visibility = View.GONE
            }

            Glide.with(binding.root.context)
                .load(banner.image_url)
                .placeholder(R.drawable.bg_rounded_card)
                .error(R.drawable.bg_rounded_card)
                .into(binding.ivBannerImage)

            binding.cardBanner.setOnClickListener {
                onBannerClick(banner)
            }
        }
    }
}
