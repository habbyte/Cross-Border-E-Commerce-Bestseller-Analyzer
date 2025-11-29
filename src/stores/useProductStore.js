/**
 * 产品状态管理 Store
 * 使用 Pinia 统一管理应用状态，提升数据一致性
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { productService } from '../services/ProductService.js'
import { SearchFilter } from '../types/index.js'
import { DemoData } from '../services/DemoData.js'
import { events } from '../analytics/events.js'
import { useOnboardingStore } from './useOnboardingStore.js'

const currencyFormatter = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY'
})

const normalizeProduct = (product = {}) => ({
  ...product,
  // 統一字段名：API 返回 title，前端使用 name
  name: product.name || product.title || '',
  title: product.title || product.name || '',
  formattedPrice: product.formattedPrice ?? currencyFormatter.format(product.price ?? 0),
  status: product.status || 'active',
  stock: typeof product.stock === 'number' ? product.stock : 0,
  profit: typeof product.profit === 'number' ? product.profit : Math.round(product.marginRate ?? 0),
  tags: Array.isArray(product.tags) ? [...product.tags] : []
})

export const useProductStore = defineStore('product', () => {
  const onboarding = useOnboardingStore()

  const products = ref([])
  const watchlist = ref(new Set())
  const currentFilter = ref(new SearchFilter())
  const selectedProducts = ref(new Set())
  const loading = ref(false)
  const error = ref(null)
  const isInitialized = ref(false)

  const filteredProducts = computed(() =>
    products.value.filter(product => currentFilter.value.matches(product))
  )

  const watchedProducts = computed(() =>
    products.value.filter(product => watchlist.value.has(product.id))
  )

  const topProducts = computed(() =>
    [...products.value]
      .sort((a, b) => {
        const scoreA = (a.marginRate ?? 0) * 0.6 + (100 - (a.competitionScore ?? 0)) * 0.4
        const scoreB = (b.marginRate ?? 0) * 0.6 + (100 - (b.competitionScore ?? 0)) * 0.4
        return scoreB - scoreA
      })
      .slice(0, 6)
  )

  const platformStats = computed(() => {
    return products.value.reduce((stats, product) => {
      const platform = product.platform || 'unknown'
      stats[platform] = (stats[platform] || 0) + 1
      return stats
    }, {})
  })

  const statistics = computed(() => {
    if (products.value.length === 0) {
      return {
        totalProducts: 0,
        averageMargin: 0,
        alertCount: 0,
        trendDirection: 'neutral',
        watchedProducts: 0,
        hotProducts: 0
      }
    }

    const totalMargin = products.value.reduce((sum, product) => sum + (product.marginRate ?? 0), 0)
    const averageMargin = totalMargin / products.value.length
    const alertCount = products.value.filter(product => (product.competitionScore ?? 0) > 50).length

    return {
      totalProducts: products.value.length,
      averageMargin: averageMargin.toFixed(1),
      alertCount,
      trendDirection: averageMargin > 20 ? 'up' : 'down',
      watchedProducts: watchlist.value.size,
      hotProducts: topProducts.value.length
    }
  })

  const compareProducts = computed(() =>
    products.value.filter(product => selectedProducts.value.has(product.id))
  )

  const setProducts = (list) => {
    products.value = list.map(normalizeProduct)
  }

  const initializeWatchlist = () => {
    const ids = productService.getWatchlist().map(product => product.id)
    watchlist.value = new Set(ids)
  }

  const ensureInitialized = async () => {
    if (!isInitialized.value) {
      await initialize()
    }
  }

  async function initialize() {
    if (isInitialized.value) return
    try {
      loading.value = true
      error.value = null
      console.log('[ProductStore] Initializing...')
      
      // 等待 ProductService 完成 API 加載（如果正在加載）
      // ProductService 在構造函數中異步加載，我們需要等待它完成
      let retries = 0
      const maxRetries = 50  // 增加重試次數，給 API 更多時間
      while (productService._loading && retries < maxRetries) {
        console.log(`[ProductStore] Waiting for ProductService to load... (${retries}/${maxRetries})`)
        await new Promise(resolve => setTimeout(resolve, 200))
        retries++
      }
      
      // 如果加載完成但沒有數據，再等待一下
      if (productService.getAllProducts().length === 0 && !productService._error) {
        console.log('[ProductStore] No products yet, waiting a bit more...')
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
      
      const allProducts = productService.getAllProducts().map(normalizeProduct)
      console.log(`[ProductStore] Loaded ${allProducts.length} products`)
      
      if (allProducts.length === 0) {
        console.warn('[ProductStore] No products loaded, this might indicate an API issue')
      }
      
      setProducts(allProducts)
      initializeWatchlist()
      isInitialized.value = true
      console.log('[ProductStore] Initialization complete')
    } catch (err) {
      error.value = err.message
      console.error('[ProductStore] Failed to initialize product store:', err)
    } finally {
      loading.value = false
    }
  }

  function loadSampleProducts() {
    const samples = DemoData.getSample().map(normalizeProduct)
    setProducts(samples)
    watchlist.value = new Set()
    selectedProducts.value.clear()
    isInitialized.value = true
    loading.value = false
    error.value = null
    events.track('products_sample_loaded', { count: samples.length })
  }

  function searchProducts(query = '', filterOptions = {}) {
    const filter = new SearchFilter({
      keyword: query,
      platform: filterOptions.platform || 'all',
      category: filterOptions.category || 'all',
      minMargin: filterOptions.minMargin || 0,
      maxCompetition: filterOptions.maxCompetition || 100
    })

    if (query || filterOptions.platform || filterOptions.category) {
      onboarding.mark('search')
    }

    return products.value.filter(product => filter.matches(product))
  }

  function addToWatchlist(productId) {
    try {
      productService.addToWatchlist(productId)
      watchlist.value.add(productId)
      onboarding.mark('monitor')
      events.track('product_watch_added', { id: productId })
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  function removeFromWatchlist(productId) {
    productService.removeFromWatchlist(productId)
    watchlist.value.delete(productId)
    events.track('product_watch_removed', { id: productId })
  }

  function toggleWatch(productId) {
    if (isWatched(productId)) {
      removeFromWatchlist(productId)
    } else {
      addToWatchlist(productId)
    }
  }

  function addToCompare(productId) {
    if (selectedProducts.value.size >= 4) {
      throw new Error('最多只能对比 4 个产品')
    }
    selectedProducts.value.add(productId)
    onboarding.mark('compare')
    events.track('product_compare_added', { id: productId })
  }

  function removeFromCompare(productId) {
    selectedProducts.value.delete(productId)
    events.track('product_compare_removed', { id: productId })
  }

  function clearCompare() {
    selectedProducts.value.clear()
  }

  async function getProduct(id) {
    // 先從本地查找
    const localProduct = products.value.find(product => product.id === id)
    if (localProduct) {
      return localProduct
    }
    
    // 本地沒有，從 API 獲取
    try {
      const product = await productService.getProduct(id)
      // 將獲取的產品添加到 store
      if (product && !products.value.find(p => p.id === product.id)) {
        products.value.push(normalizeProduct(product))
      }
      return normalizeProduct(product)
    } catch (error) {
      console.error(`[ProductStore] Failed to get product ${id}:`, error)
      throw error
    }
  }

  const getById = getProduct

  async function toggleStatus(productId) {
    // 先從本地查找，如果沒有則從 API 獲取
    let product = products.value.find(p => p.id === productId)
    if (!product) {
      try {
        product = await getProduct(productId)
      } catch (error) {
        console.error(`[ProductStore] Cannot toggle status for product ${productId}:`, error)
        return
      }
    }
    if (!product) return
    product.status = product.status === 'active' ? 'inactive' : 'active'
    events.track('product_status_toggled', { id: productId, status: product.status })
  }

  function isWatched(productId) {
    return watchlist.value.has(productId)
  }

  function isInCompare(productId) {
    return selectedProducts.value.has(productId)
  }

  function resetFilter() {
    currentFilter.value = new SearchFilter()
  }

  function clearError() {
    error.value = null
  }

  return {
    products,
    watchlist,
    currentFilter,
    selectedProducts,
    loading,
    error,
    isInitialized,
    filteredProducts,
    watchedProducts,
    topProducts,
    statistics,
    platformStats,
    compareProducts,
    initialize,
    ensureInitialized,
    loadSampleProducts,
    searchProducts,
    addToWatchlist,
    removeFromWatchlist,
    toggleWatch,
    addToCompare,
    removeFromCompare,
    clearCompare,
    getProduct,
    getById,
    toggleStatus,
    isWatched,
    isInCompare,
    resetFilter,
    clearError
  }
})
