package com.betasan.exporttracker.data

import android.content.Context
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ExportApiClient {
    const val DEFAULT_BASE_URL = "https://betasan-export.onrender.com/api/"
    private const val PREFS_NAME = "betasan_export_prefs"
    private const val KEY_BASE_URL = "custom_base_url"

    private var retrofit: Retrofit? = null
    private var currentUrl: String = ""

    fun getBaseUrl(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL) ?: DEFAULT_BASE_URL
    }

    fun setBaseUrl(context: Context, url: String) {
        val formatted = if (url.endsWith("/")) url else "$url/"
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_BASE_URL, formatted).apply()
        retrofit = null
    }

    fun getApiService(context: Context): ExportApiService {
        val url = getBaseUrl(context)
        if (retrofit == null || currentUrl != url) {
            currentUrl = url
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }

            val client = OkHttpClient.Builder()
                .addInterceptor(logging)
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(15, TimeUnit.SECONDS)
                .build()

            retrofit = Retrofit.Builder()
                .baseUrl(url)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
        }
        return retrofit!!.create(ExportApiService::class.java)
    }
}
