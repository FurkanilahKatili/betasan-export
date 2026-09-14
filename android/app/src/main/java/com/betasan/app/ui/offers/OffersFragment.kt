package com.betasan.app.ui.offers

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.GridLayoutManager
import com.betasan.app.data.MockDataProvider
import com.betasan.app.data.api.ApiClient
import com.betasan.app.data.cart.CartManager
import com.betasan.app.data.model.Product
import com.betasan.app.databinding.FragmentOffersBinding
import com.betasan.app.ui.adapter.ProductAdapter
import com.betasan.app.ui.detail.ProductDetailActivity
import kotlinx.coroutines.launch

class OffersFragment : Fragment() {

    private var _binding: FragmentOffersBinding? = null
    private val binding get() = _binding!!

    private lateinit var productAdapter: ProductAdapter

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentOffersBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

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

        binding.rvOffersList.layoutManager = GridLayoutManager(requireContext(), 2)
        binding.rvOffersList.adapter = productAdapter

        binding.swipeRefreshOffers.setOnRefreshListener {
            loadOffers()
        }

        loadOffers()
    }

    private fun loadOffers() {
        binding.swipeRefreshOffers.isRefreshing = true
        binding.layoutEmptyOffers.visibility = View.GONE

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val res = ApiClient.service.getProducts(onlyDiscounted = 1)
                val discounted = if (res.success && !res.data.isNullOrEmpty()) {
                    res.data
                } else {
                    MockDataProvider.getProducts().filter { it.discount_rate > 0 }
                }

                if (discounted.isNotEmpty()) {
                    productAdapter.updateData(discounted)
                    binding.rvOffersList.visibility = View.VISIBLE
                    binding.layoutEmptyOffers.visibility = View.GONE
                } else {
                    productAdapter.updateData(emptyList())
                    binding.rvOffersList.visibility = View.GONE
                    binding.layoutEmptyOffers.visibility = View.VISIBLE
                }
            } catch (e: Exception) {
                val mockDiscounted = MockDataProvider.getProducts().filter { it.discount_rate > 0 }
                if (mockDiscounted.isNotEmpty()) {
                    productAdapter.updateData(mockDiscounted)
                    binding.rvOffersList.visibility = View.VISIBLE
                    binding.layoutEmptyOffers.visibility = View.GONE
                } else {
                    binding.layoutEmptyOffers.visibility = View.VISIBLE
                }
            } finally {
                _binding?.let {
                    it.swipeRefreshOffers.isRefreshing = false
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
