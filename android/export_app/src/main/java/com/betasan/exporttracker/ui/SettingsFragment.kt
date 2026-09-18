package com.betasan.exporttracker.ui

import android.app.AlertDialog
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.betasan.exporttracker.R
import com.betasan.exporttracker.data.ExportApiClient
import com.betasan.exporttracker.databinding.FragmentSettingsBinding
import com.betasan.exporttracker.service.ExportWorkScheduler

class SettingsFragment : Fragment() {

    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentSettingsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val currentInterval = ExportWorkScheduler.getSavedIntervalHours(requireContext())
        if (currentInterval == 6L) {
            binding.rb6Hours.isChecked = true
        } else {
            binding.rb2Hours.isChecked = true
        }

        binding.rgInterval.setOnCheckedChangeListener { _, checkedId ->
            val hours = if (checkedId == R.id.rb6Hours) 6L else 2L
            ExportWorkScheduler.setSavedIntervalHours(requireContext(), hours)
            Toast.makeText(requireContext(), "Bildirim sıklığı: $hours Saatte Bir olarak güncellendi", Toast.LENGTH_SHORT).show()
        }

        binding.btnTestNotification.setOnClickListener {
            ExportWorkScheduler.triggerTestNotificationNow(requireContext())
            Toast.makeText(requireContext(), "Test bildirimi tetiklendi! Birkaç saniye içinde bildirim gelecek...", Toast.LENGTH_LONG).show()
        }

        binding.btnBatteryOptimization.setOnClickListener {
            ExportWorkScheduler.requestIgnoreBatteryOptimizations(requireContext())
        }

        binding.btnDownloadExcelReport.setOnClickListener {
            downloadAndOpenExcelReport()
        }

        binding.tvServerUrl.text = ExportApiClient.getBaseUrl(requireContext())
        binding.btnChangeUrl.setOnClickListener {
            showUrlDialog()
        }
    }

    private fun downloadAndOpenExcelReport() {
        val baseUrl = ExportApiClient.getBaseUrl(requireContext())
        val reportUrl = if (baseUrl.endsWith("/")) baseUrl + "exports/report/excel" else "$baseUrl/exports/report/excel"
        try {
            val intent = android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(reportUrl))
            startActivity(intent)
            Toast.makeText(requireContext(), "Excel raporu indiriliyor...", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(requireContext(), "Rapor bağlantısı açılamadı: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun showUrlDialog() {
        val input = EditText(requireContext()).apply {
            setText(ExportApiClient.getBaseUrl(requireContext()))
            setSelection(text.length)
        }

        AlertDialog.Builder(requireContext())
            .setTitle("API Sunucu Adresi")
            .setMessage("Canlı Render veya yerel sunucu adresini girin:")
            .setView(input)
            .setPositiveButton("Kaydet") { _, _ ->
                val newUrl = input.text.toString().trim()
                if (newUrl.isNotEmpty()) {
                    ExportApiClient.setBaseUrl(requireContext(), newUrl)
                    binding.tvServerUrl.text = ExportApiClient.getBaseUrl(requireContext())
                    Toast.makeText(requireContext(), "Sunucu adresi güncellendi!", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("İptal", null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
