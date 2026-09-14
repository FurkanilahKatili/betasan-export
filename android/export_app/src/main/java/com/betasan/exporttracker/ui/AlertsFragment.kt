package com.betasan.exporttracker.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.betasan.exporttracker.data.ExportAlert
import com.betasan.exporttracker.data.ExportApiClient
import com.betasan.exporttracker.databinding.FragmentAlertsBinding
import kotlinx.coroutines.launch

class AlertsFragment : Fragment() {

    private var _binding: FragmentAlertsBinding? = null
    private val binding get() = _binding!!
    private lateinit var adapter: AlertAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentAlertsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = AlertAdapter()
        binding.rvAlerts.layoutManager = LinearLayoutManager(requireContext())
        binding.rvAlerts.adapter = adapter

        loadAlerts()
    }

    private fun loadAlerts() {
        lifecycleScope.launch {
            try {
                val api = ExportApiClient.getApiService(requireContext())
                val response = api.getExports()
                if (response.isSuccessful) {
                    val shipments = response.body()?.data ?: emptyList()
                    val alerts = mutableListOf<ExportAlert>()

                    for (s in shipments) {
                        try {
                            val detail = api.getExportDetail(s.id)
                            detail.body()?.alerts?.let { alerts.addAll(it) }
                        } catch (_: Exception) {}
                    }
                    adapter.updateList(alerts)
                }
            } catch (_: Exception) {}
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
