package com.betasan.app.data.api

import android.content.Context
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    private const val PREF_NAME = "betasan_api_pref"
    private const val KEY_BASE_URL = "custom_base_url"

    var BASE_URL: String = "https://demo.betasan.com/api/"
        private set

    const val DEFAULT_WHATSAPP_NUMBER = "905000000000"
    const val DEFAULT_EMAIL_ADDRESS = "siparis@betasan.com.tr"

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(5, TimeUnit.SECONDS)
        .build()

    private var _service: ApiService? = null

    val service: ApiService
        get() {
            if (_service == null) {
                val retrofit = Retrofit.Builder()
                    .baseUrl(BASE_URL)
                    .client(okHttpClient)
                    .addConverterFactory(GsonConverterFactory.create())
                    .build()
                _service = retrofit.create(ApiService::class.java)
            }
            return _service!!
        }

    fun init(context: Context) {
        val prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
        val saved = prefs.getString(KEY_BASE_URL, null)
        if (!saved.isNullOrBlank()) {
            BASE_URL = saved
            _service = null
        }
    }

    fun updateBaseUrl(context: Context, newUrl: String) {
        val formatted = if (newUrl.endsWith("/")) newUrl else "$newUrl/"
        BASE_URL = formatted
        _service = null
        val prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_BASE_URL, formatted).apply()
    }
}
