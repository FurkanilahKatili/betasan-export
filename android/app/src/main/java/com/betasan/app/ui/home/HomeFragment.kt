package com.betasan.app.ui.home

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.LinearLayoutManager
import com.betasan.app.MainActivity
import com.betasan.app.R
import com.betasan.app.data.MockDataProvider
import com.betasan.app.data.api.ApiClient
import com.betasan.app.data.cart.CartManager
import com.betasan.app.data.model.Category
import com.betasan.app.data.model.Product
import com.betasan.app.databinding.FragmentHomeBinding
import com.betasan.app.ui.adapter.BannerAdapter
import com.betasan.app.ui.adapter.CategoryAdapter
import com.betasan.app.ui.adapter.ProductAdapter
import com.betasan.app.ui.detail.ProductDetailActivity
import kotlinx.coroutines.launch

class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!

    private lateinit var bannerAdapter: BannerAdapter
    private lateinit var categoryAdapter: CategoryAdapter
    private lateinit var offersAdapter: ProductAdapter
    private lateinit var featuredAdapter: ProductAdapter

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        setupRecyclerViews()
        setupListeners()
        loadData()
    }

    private fun setupRecyclerViews() {
        // Banner Slider
        bannerAdapter = BannerAdapter { banner ->
            banner.product_id?.let { pid ->
                openProductDetailById(pid)
            }
        }
        binding.rvBanners.layoutManager = LinearLayoutManager(requireContext(), LinearLayoutManager.HORIZONTAL, false)
        binding.rvBanners.adapter = bannerAdapter

        // Kategoriler
        categoryAdapter = CategoryAdapter { category ->
            // Kategoriye tıklandığında Katalog sekmesine yönlendir
            (activity as? MainActivity)?.navigateToCatalogWithCategory(category?.id)
        }
        binding.rvCategories.layoutManager = LinearLayoutManager(requireContext(), LinearLayoutManager.HORIZONTAL, false)
        binding.rvCategories.adapter = categoryAdapter

        // İndirim Fırsatları
        offersAdapter = ProductAdapter(
            onProductClick = { openProductDetail(it) },
            onAddToCartClick = { addToCart(it) }
        )
        binding.rvOffers.layoutManager = LinearLayoutManager(requireContext(), LinearLayoutManager.HORIZONTAL, false)
        binding.rvOffers.adapter = offersAdapter

        // Öne Çıkan Ürünler (2 Kolonlu Izgara)
        featuredAdapter = ProductAdapter(
            onProductClick = { openProductDetail(it) },
            onAddToCartClick = { addToCart(it) }
        )
        binding.rvFeaturedProducts.layoutManager = GridLayoutManager(requireContext(), 2)
        binding.rvFeaturedProducts.adapter = featuredAdapter
    }

    private fun setupListeners() {
        binding.swipeRefresh.setOnRefreshListener {
            loadData()
        }

        binding.btnSeeAllOffers.setOnClickListener {
            (activity as? MainActivity)?.navigateToOffers()
        }
    }

    private fun loadData() {
        binding.swipeRefresh.isRefreshing = true

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                // Bannerları Çek
                val banners = try {
                    val res = ApiClient.service.getBanners()
                    if (res.success && !res.data.isNullOrEmpty()) res.data else MockDataProvider.getBanners()
                } catch (e: Exception) {
                    MockDataProvider.getBanners()
                }
                bannerAdapter.updateData(banners)
                binding.rvBanners.visibility = View.VISIBLE

                // Kategorileri Çek
                val categories = try {
                    val res = ApiClient.service.getCategories()
                    if (res.success && !res.data.isNullOrEmpty()) res.data else MockDataProvider.getCategories()
                } catch (e: Exception) {
                    MockDataProvider.getCategories()
                }
                categoryAdapter.updateData(categories)

                // Ürünleri Çek
                val allProducts = try {
                    val res = ApiClient.service.getProducts()
                    if (res.success && !res.data.isNullOrEmpty()) res.data else MockDataProvider.getProducts()
                } catch (e: Exception) {
                    MockDataProvider.getProducts()
                }

                val discounted = allProducts.filter { it.discount_rate > 0 }
                if (discounted.isNotEmpty()) {
                    offersAdapter.updateData(discounted)
                    binding.layoutOffersHeader.visibility = View.VISIBLE
                    binding.rvOffers.visibility = View.VISIBLE
                } else {
                    binding.layoutOffersHeader.visibility = View.GONE
                    binding.rvOffers.visibility = View.GONE
                }

                val featured = allProducts.filter { it.is_featured }.ifEmpty { allProducts }
                featuredAdapter.updateData(featured)

            } catch (e: Exception) {
                // Güvenli fallback
                bannerAdapter.updateData(MockDataProvider.getBanners())
                categoryAdapter.updateData(MockDataProvider.getCategories())
                val products = MockDataProvider.getProducts()
                offersAdapter.updateData(products.filter { it.discount_rate > 0 })
                featuredAdapter.updateData(products)
            } finally {
                _binding?.let {
                    it.swipeRefresh.isRefreshing = false
                }
            }
        }
    }

    private fun openProductDetail(product: Product) {
        val intent = Intent(requireContext(), ProductDetailActivity::class.java).apply {
            putExtra(ProductDetailActivity.EXTRA_PRODUCT, product)
        }
        startActivity(intent)
    }

    private fun openProductDetailById(productId: Int) {
        val intent = Intent(requireContext(), ProductDetailActivity::class.java).apply {
            putExtra(ProductDetailActivity.EXTRA_PRODUCT_ID, productId)
        }
        startActivity(intent)
    }

    private fun addToCart(product: Product) {
        CartManager.getInstance(requireContext()).addToCart(product, 1)
        Toast.makeText(requireContext(), "${product.name} sepete eklendi!", Toast.LENGTH_SHORT).show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
