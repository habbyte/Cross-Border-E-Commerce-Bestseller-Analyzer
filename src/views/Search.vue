<template>
  <div class="search-page">
    <!-- 椤甸潰鏍囬 -->
    <div class="page-header">
      <h1 class="page-title">{{ $t('search.title') }}</h1>
      <p class="page-subtitle">{{ $t('search.subtitle') }}</p>
    </div>
    
    <!-- 鎼滅储鍜岀瓫閫?-->
    <div class="search-section">
      <div class="search-form">
        <!-- 鎼滅储妗?-->
        <div class="search-input-group">
          <input
            v-model="searchQuery"
            type="text"
            class="form-input search-input"
            :placeholder="$t('search.placeholder')"
            @keyup.enter="handleSearch"
          />
          <button 
            class="btn btn-primary search-btn"
            @click="handleSearch"
            :disabled="loading"
          >
            {{ loading ? $t('search.searching') : $t('search.searchButton') }}
          </button>
        </div>
        
        <!-- 绛涢€夊櫒 -->
        <div class="filters">
          <div class="filter-group">
            <label class="filter-label">{{ $t('search.platform') }}</label>
            <select v-model="filters.platform" class="form-select">
              <option value="">{{ $t('search.allPlatforms') }}</option>
              <option v-for="platform in platforms" :key="platform" :value="platform">
                {{ translatePlatform(platform) }}
              </option>
            </select>
          </div>
          
          <div class="filter-group">
            <label class="filter-label">{{ $t('search.category') }}</label>
            <select v-model="filters.category" class="form-select">
              <option value="">{{ $t('search.allCategories') }}</option>
              <option v-for="category in categories" :key="category" :value="category">
                {{ category }}
              </option>
            </select>
          </div>
          
          <div class="filter-group">
            <label class="filter-label">{{ $t('search.priceRange') }}</label>
            <select v-model="filters.priceRange" class="form-select">
              <option value="">{{ $t('search.noPriceLimit') }}</option>
              <option value="0-50">{{ $t('search.priceRanges.range0_50') }}</option>
              <option value="50-100">{{ $t('search.priceRanges.range50_100') }}</option>
              <option value="100-200">{{ $t('search.priceRanges.range100_200') }}</option>
              <option value="200+">{{ $t('search.priceRanges.range200_plus') }}</option>
            </select>
          </div>
          
          <div class="filter-group">
            <label class="filter-label">{{ $t('search.competition') }}</label>
            <select v-model="filters.competition" class="form-select">
              <option value="">{{ $t('common.all') }}</option>
              <option value="low">{{ $t('productDetail.competition.low') }}</option>
              <option value="medium">{{ $t('productDetail.competition.medium') }}</option>
              <option value="high">{{ $t('productDetail.competition.high') }}</option>
            </select>
          </div>
          
          <button 
            class="btn btn-secondary"
            @click="clearFilters"
          >
            {{ $t('search.clearFilters') }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 鎼滅储缁撴灉 -->
    <div class="results-section">
      <!-- 缁撴灉缁熻 -->
      <div class="results-header">
        <div class="results-info">
          <span class="results-count">{{ $t('search.resultsCount', { count: filteredProducts.length }) }}</span>
          <span v-if="searchQuery" class="search-term">
            {{ $t('search.keyword') }}: "{{ searchQuery }}"
          </span>
        </div>
        
        <div class="results-actions">
          <select v-model="sortBy" class="form-select">
            <option value="relevance">{{ $t('search.sortBy.relevance') }}</option>
            <option value="sales">{{ $t('search.sortBy.sales') }}</option>
            <option value="price">{{ $t('search.sortBy.price') }}</option>
            <option value="rating">{{ $t('search.sortBy.rating') }}</option>
            <option value="competition">{{ $t('search.sortBy.competition') }}</option>
          </select>
          
          <button 
            class="btn btn-ghost view-toggle"
            @click="toggleView"
          >
            {{ viewMode === 'grid' ? '📋' : '🗂️' }}
          </button>
        </div>
      </div>
      
      <!-- 鍟嗗搧鍒楄〃 -->
      <div v-if="filteredProducts.length > 0" class="results-content">
        <!-- 缃戞牸瑙嗗浘 -->
        <div v-if="viewMode === 'grid'" class="products-grid">
          <ProductCard
            v-for="product in paginatedProducts"
            :key="product.id"
            :product="product"
            :is-watched="isWatched(product.id)"
            :is-in-compare="isInCompare(product.id)"
            @view-details="viewProductDetails"
            @add-to-watch="toggleWatch"
            @add-to-compare="addToCompare"
          />
        </div>
        
        <!-- 鍒楄〃瑙嗗浘 -->
        <div v-else class="products-table">
          <DataTable
            title=""
            :columns="tableColumns"
            :data="paginatedTableRows"
            :empty-text="$t('search.noResults')"
            @row-click="viewProductDetails"
            @sort-change="handleSort"
          />
        </div>
        
        <!-- 鍒嗛〉 -->
        <div v-if="totalPages > 1" class="pagination">
          <button 
            class="btn btn-ghost"
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
          >
            {{ $t('common.previous') }}
          </button>
          
          <div class="page-numbers">
            <button
              v-for="page in visiblePages"
              :key="page"
              class="btn"
              :class="page === currentPage ? 'btn-primary' : 'btn-ghost'"
              @click="goToPage(page)"
            >
              {{ page }}
            </button>
          </div>
          
          <button 
            class="btn btn-ghost"
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
            {{ $t('common.next') }}
          </button>
        </div>
      </div>
      
      <!-- 绌虹姸鎬?-->
      <div v-else class="empty-results">
        <div class="empty-icon">馃攳</div>
        <div class="empty-title">{{ $t('search.noResults') }}</div>
        <div class="empty-text">
          {{ $t('search.noResultsDesc') }}
        </div>
        <button class="btn btn-primary" @click="clearFilters">
          {{ $t('search.clearAllFilters') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ProductCard from '../components/ProductCard.vue'
import DataTable from '../components/DataTable.vue'
import { useProductStore } from '../stores/useProductStore.js'
import { PLATFORMS } from '@/types/index.js'

const resolveCompetitionLimit = (level) => {
  if (level === 'low') return 30
  if (level === 'medium') return 60
  if (level === 'high') return 100
  return 100
}

const parsePriceRange = (range) => {
  if (!range) {
    return [null, null]
  }

  if (range === '200+') {
    return [200, null]
  }

  const [min, max] = range.split('-').map(Number)

  return [
    Number.isFinite(min) ? min : null,
    Number.isFinite(max) ? max : null
  ]
}

const getSalesEstimate = (product) => {
  if (typeof product.sales === 'number') {
    return product.sales
  }
  return Math.round(product.marginRate * 25 + 150)
}

const getRatingEstimate = (product) => {
  if (typeof product.rating === 'number') {
    return product.rating
  }
  const rating = 4.8 - (product.competitionScore / 100) * 1.5
  return Number(Math.max(3, Math.min(5, rating)).toFixed(1))
}

export default {
  name: 'Search',
  components: {
    ProductCard,
    DataTable
  },
  setup() {
    const router = useRouter()
    const { t } = useI18n()
    const productStore = useProductStore()

    const basePlatforms = [
      PLATFORMS.AMAZON,
      PLATFORMS.SHOPEE,
      PLATFORMS.LAZADA,
      PLATFORMS.EBAY,
      PLATFORMS.ALIEXPRESS
    ]

    const searchQuery = ref('')
    const filters = reactive({
      platform: '',
      category: '',
      priceRange: '',
      competition: ''
    })
    const sortBy = ref('relevance')
    const sortOrder = ref('desc')
    const viewMode = ref('grid')
    const currentPage = ref(1)
    const pageSize = ref(12)

    const loading = computed(() => productStore.loading)

    const tableColumns = computed(() => ([
      { key: 'title', label: t('search.table.name'), sortable: true },
      { key: 'platform', label: t('search.table.platform'), sortable: true },
      { key: 'formattedPrice', label: t('search.table.price'), sortable: true },
      { key: 'sales', label: t('search.table.sales'), sortable: true },
      { key: 'rating', label: t('search.table.rating'), sortable: true },
      { key: 'competition', label: t('search.table.competition'), sortable: true }
    ]))

    const platforms = computed(() => {
      const dynamic = Array.from(new Set(productStore.products.map(product => product.platform)))
      return Array.from(new Set([...basePlatforms, ...dynamic]))
    })

    const translatePlatform = (value) => {
      const key = `settings.platforms.${value}`
      const translated = t(key)
      return translated === key ? value : translated
    }

    const categories = computed(() => {
      const unique = new Set(productStore.products.map(product => product.category))
      return Array.from(unique)
    })

    const filteredProducts = computed(() => {
      const [minPrice, maxPrice] = parsePriceRange(filters.priceRange)
      const results = productStore.searchProducts(searchQuery.value, {
        platform: filters.platform || 'all',
        category: filters.category || 'all',
        minMargin: 0,
        maxCompetition: resolveCompetitionLimit(filters.competition)
      })

      return results.filter(product => {
        if (minPrice !== null && product.price < minPrice) {
          return false
        }

        if (maxPrice !== null && product.price > maxPrice) {
          return false
        }

        return true
      })
    })

    const sortedProducts = computed(() => {
      const products = [...filteredProducts.value]
      const direction = sortOrder.value === 'asc' ? 1 : -1

      switch (sortBy.value) {
        case 'sales':
          return products.sort((a, b) => (getSalesEstimate(a) - getSalesEstimate(b)) * direction)
        case 'price':
          return products.sort((a, b) => (a.price - b.price) * direction)
        case 'rating':
          return products.sort((a, b) => (getRatingEstimate(a) - getRatingEstimate(b)) * direction)
        case 'competition':
          return products.sort((a, b) => (a.competitionScore - b.competitionScore) * direction)
        default:
          return products
      }
    })

    const totalPages = computed(() => Math.max(1, Math.ceil(sortedProducts.value.length / pageSize.value)))

    const paginatedProducts = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      return sortedProducts.value.slice(start, start + pageSize.value)
    })

    const tableRows = computed(() => {
      return sortedProducts.value.map(product => ({
        id: product.id,
        title: product.title,
        platform: translatePlatform(product.platform),
        formattedPrice: product.formattedPrice,
        sales: getSalesEstimate(product),
        rating: getRatingEstimate(product),
        competition: product.competitionLevel
      }))
    })

    const paginatedTableRows = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      return tableRows.value.slice(start, start + pageSize.value)
    })

    const visiblePages = computed(() => {
      const pages = []
      const total = totalPages.value
      const current = currentPage.value
      const delta = 2
      const start = Math.max(1, current - delta)
      const end = Math.min(total, current + delta)

      for (let page = start; page <= end; page += 1) {
        pages.push(page)
      }

      return pages
    })

    const handleSearch = () => {
      currentPage.value = 1
    }

    const clearFilters = () => {
      filters.platform = ''
      filters.category = ''
      filters.priceRange = ''
      filters.competition = ''
      handleSearch()
    }

    const toggleView = () => {
      viewMode.value = viewMode.value === 'grid' ? 'table' : 'grid'
    }

    const goToPage = (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page
      }
    }

    const viewProductDetails = (item) => {
      const id = typeof item === 'string' ? item : item?.id
      if (id) {
        router.push(`/products/${id}`)
      }
    }

    const toggleWatch = (productId) => {
      try {
        productStore.toggleWatch(productId)
      } catch (error) {
        console.error('Failed to toggle watchlist:', error)
      }
    }

    const addToCompare = (productId) => {
      try {
        productStore.addToCompare(productId)
      } catch (error) {
        console.error('Failed to add product to compare:', error)
      }
    }

    const handleSort = ({ key, order }) => {
      sortBy.value = key
      sortOrder.value = order === 'asc' ? 'asc' : 'desc'
      currentPage.value = 1
    }

    watch(
      [searchQuery, () => filters.platform, () => filters.category, () => filters.priceRange, () => filters.competition],
      () => {
        currentPage.value = 1
      }
    )

    watch(sortBy, (value, previous) => {
      if (value === 'relevance') {
        sortOrder.value = 'desc'
      } else if ((value === 'price' || value === 'competition') && value !== previous) {
        sortOrder.value = 'asc'
      } else if (value !== previous) {
        sortOrder.value = 'desc'
      }
    })

    return {
      t,
      loading,
      searchQuery,
      filters,
      sortBy,
      sortOrder,
      viewMode,
      currentPage,
      pageSize,
      tableColumns,
      platforms,
      categories,
      filteredProducts,
      paginatedProducts,
      paginatedTableRows,
      totalPages,
      visiblePages,
      handleSearch,
      clearFilters,
      toggleView,
      goToPage,
      viewProductDetails,
      toggleWatch,
      addToCompare,
      handleSort,
      translatePlatform,
      isWatched: productStore.isWatched,
      isInCompare: productStore.isInCompare
    }
  }
}

</script>

<style scoped>
.search-page {
  max-width: 1200px;
  margin: 0 auto;
}

/* 椤甸潰澶撮儴 */
.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 16px;
  color: var(--color-text-muted);
  margin: 0;
}

/* 鎼滅储鍖哄煙 */
.search-section {
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
  margin-bottom: 24px;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-input-group {
  display: flex;
  gap: 12px;
}

.search-input {
  flex: 1;
  font-size: 16px;
  padding: 12px 16px;
}

.search-btn {
  padding: 12px 24px;
  font-size: 16px;
  white-space: nowrap;
}

/* 绛涢€夊櫒 */
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 120px;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

/* 缁撴灉鍖哄煙 */
.results-section {
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f3f4f6;
}

.results-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.results-count {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.search-term {
  font-size: 14px;
  color: var(--color-text-muted);
}

.results-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-toggle {
  padding: 8px;
  font-size: 16px;
}

/* 鍟嗗搧缃戞牸 */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

/* 鍟嗗搧琛ㄦ牸 */
.products-table {
  margin-bottom: 24px;
}

/* 鍒嗛〉 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.page-numbers {
  display: flex;
  gap: 4px;
}

/* 绌虹姸鎬?*/
.empty-results {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}

.empty-text {
  font-size: 16px;
  color: var(--color-text-muted);
  margin-bottom: 24px;
}

/* 鍝嶅簲寮忚璁?*/
@media (max-width: 768px) {
  .search-input-group {
    flex-direction: column;
  }
  
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-group {
    min-width: auto;
  }
  
  .results-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .results-actions {
    justify-content: space-between;
  }
  
  .products-grid {
    grid-template-columns: 1fr;
  }
  
  .pagination {
    flex-wrap: wrap;
    gap: 4px;
  }
  
  .page-numbers {
    order: -1;
    width: 100%;
    justify-content: center;
  }
}
</style>
