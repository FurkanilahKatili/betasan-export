package com.betasan.app.ui.catalog

import android.content.Intent
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.LinearLayoutManager
import com.betasan.app.data.MockDataProvider
import com.betasan.app.data.api.ApiClient
import com.betasan.app.data.cart.CartManager
import com.betasan.app.data.model.Product
import com.betasan.app.databinding.FragmentCatalogBinding
import com.betasan.app.ui.adapter.CategoryAdapter
import com.betasan.app.ui.adapter.ProductAdapter
import com.betasan.app.ui.detail.ProductDetailActivity
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class CatalogFragment : Fragment() {

    private var _binding: FragmentCatalogBinding? = null
    private val binding get() = _binding!!

    private lateinit var categoryAdapter: CategoryAdapter
    private lateinit var productAdapter: ProductAdapter

    private var selectedCategoryId: Int? = null
    private var searchQuery: String = ""
    private var searchJob: Job? = null

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentCatalogBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        setupRecyclerViews()
        setupSearch()
        loadCategories()
        loadProducts()

        binding.swipeRefreshCatalog.setOnRefreshListener {
            loadProducts()
        }
    }

    private fun setupRecyclerViews() {
        categoryAdapter = CategoryAdapter(
            onCategorySelected = { category ->
                selectedCategoryId = category?.id
                loadProducts()
            }
        )
        binding.rvCatalogCategories.layoutManager =
            LinearLayoutManager(requireContext(), LinearLayoutManager.HORIZONTAL, false)
        binding.rvCatalogCategories.adapter = categoryAdapter

        productAdapter = ProductAdapter(
            onProductClick = { product ->
                val intent = Intent(requireContext(), ProductDetailActivity::class.java).apply {
                    putExtra(ProductDetailActivity.EXTRA_PRODUCT, product)
                }
                startActivity(intent)
            },
            onAddToCartClick = { product ->
                CartManager.getInstance(requireContext()).addToCart(product, 1)
                Toast.makeText(requireContext(), "${product.name} sepete eklendi!", Toast.LENGTH_SHORT).show()
            }
        )
        binding.rvCatalogProducts.layoutManager = GridLayoutManager(requireContext(), 2)
        binding.rvCatalogProducts.adapter = productAdapter
    }

    private fun setupSearch() {
        binding.etSearch.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                searchJob?.cancel()
                searchJob = viewLifecycleOwner.lifecycleScope.launch {
                    delay(300) // 300ms debounce
                    searchQuery = s?.toString()?.trim() ?: ""
                    loadProducts()
                }
            }
            override fun afterTextChanged(s: Editable?) {}
        })
    }

    private fun loadCategories() {
        viewLifecycleOwner.lifecycleScope.launch {
            val categories = try {
                val res = ApiClient.service.getCategories()
                if (res.success && !res.data.isNullOrEmpty()) res.data else MockDataProvider.getCategories()
            } catch (e: Exception) {
                MockDataProvider.getCategories()
            }
            categoryAdapter.updateData(categories, selectedCategoryId)
        }
    }

    fun selectCategory(categoryId: Int?) {
        this.selectedCategoryId = categoryId
        categoryAdapter.setSelectedCategory(categoryId)
        loadProducts()
    }

    private fun loadProducts() {
        binding.swipeRefreshCatalog.isRefreshing = true
        binding.layoutEmptyCatalog.visibility = View.GONE

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val res = ApiClient.service.getProducts(
                    categoryId = selectedCategoryId,
                    search = if (searchQuery.isNotBlank()) searchQuery else null
                )

                if (res.success && !res.data.isNullOrEmpty()) {
                    productAdapter.updateData(res.data)
                    binding.rvCatalogProducts.visibility = View.VISIBLE
                    binding.layoutEmptyCatalog.visibility = View.GONE
                } else {
                    fallbackToMockProducts()
                }
            } catch (e: Exception) {
                fallbackToMockProducts()
            } finally {
                _binding?.let {
                    it.swipeRefreshCatalog.isRefreshing = false
                }
            }
        }
    }

    private fun fallbackToMockProducts() {
        var filtered = MockDataProvider.getProducts()
        if (selectedCategoryId != null) {
            filtered = filtered.filter { it.category_id == selectedCategoryId }
        }
        if (searchQuery.isNotBlank()) {
            val query = searchQuery.lowercase()
            filtered = filtered.filter { 
                it.name.lowercase().contains(query) || (it.code?.lowercase()?.contains(query) == true)
            }
        }

        if (filtered.isNotEmpty()) {
            productAdapter.updateData(filtered)
            binding.rvCatalogProducts.visibility = View.VISIBLE
            binding.layoutEmptyCatalog.visibility = View.GONE
        } else {
            productAdapter.updateData(emptyList())
            binding.rvCatalogProducts.visibility = View.GONE
            binding.layoutEmptyCatalog.visibility = View.VISIBLE
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
