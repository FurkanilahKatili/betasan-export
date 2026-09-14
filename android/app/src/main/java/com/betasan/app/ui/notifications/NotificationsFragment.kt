package com.betasan.app.ui.notifications

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.betasan.app.data.MockDataProvider
import com.betasan.app.data.api.ApiClient
import com.betasan.app.databinding.FragmentNotificationsBinding
import com.betasan.app.ui.adapter.NotificationAdapter
import com.betasan.app.ui.detail.ProductDetailActivity
import kotlinx.coroutines.launch

class NotificationsFragment : Fragment() {

    private var _binding: FragmentNotificationsBinding? = null
    private val binding get() = _binding!!

    private lateinit var notificationAdapter: NotificationAdapter

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentNotificationsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        notificationAdapter = NotificationAdapter { productId ->
            val intent = Intent(requireContext(), ProductDetailActivity::class.java).apply {
                putExtra(ProductDetailActivity.EXTRA_PRODUCT_ID, productId)
            }
            startActivity(intent)
        }

        binding.rvNotifications.layoutManager = LinearLayoutManager(requireContext())
        binding.rvNotifications.adapter = notificationAdapter

        binding.swipeRefreshNotifs.setOnRefreshListener {
            loadNotifications()
        }

        binding.cardExportSettings.setOnClickListener {
            (activity as? com.betasan.app.MainActivity)?.showExportNotificationSettingsDialog()
        }

        updateIntervalDescription()
        loadNotifications()
    }

    override fun onResume() {
        super.onResume()
        updateIntervalDescription()
    }

    private fun updateIntervalDescription() {
        val ctx = context ?: return
        val hours = com.betasan.app.service.ExportWorkScheduler.getSavedIntervalHours(ctx)
        binding.tvExportIntervalDesc.text = "${hours} Saatte Bir • Arka planda otomatik çalışır"
    }

    private fun loadNotifications() {
        binding.swipeRefreshNotifs.isRefreshing = true
        binding.layoutEmptyNotifs.visibility = View.GONE

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val res = ApiClient.service.getNotifications()
                val notifs = if (res.success && !res.data.isNullOrEmpty()) {
                    res.data
                } else {
                    MockDataProvider.getNotifications()
                }

                if (notifs.isNotEmpty()) {
                    notificationAdapter.updateData(notifs)
                    binding.rvNotifications.visibility = View.VISIBLE
                    binding.layoutEmptyNotifs.visibility = View.GONE
                } else {
                    notificationAdapter.updateData(emptyList())
                    binding.rvNotifications.visibility = View.GONE
                    binding.layoutEmptyNotifs.visibility = View.VISIBLE
                }
            } catch (e: Exception) {
                val mockNotifs = MockDataProvider.getNotifications()
                if (mockNotifs.isNotEmpty()) {
                    notificationAdapter.updateData(mockNotifs)
                    binding.rvNotifications.visibility = View.VISIBLE
                    binding.layoutEmptyNotifs.visibility = View.GONE
                } else {
                    binding.layoutEmptyNotifs.visibility = View.VISIBLE
                }
            } finally {
                _binding?.let {
                    it.swipeRefreshNotifs.isRefreshing = false
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
