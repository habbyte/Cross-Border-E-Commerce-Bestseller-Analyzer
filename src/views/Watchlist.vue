<template>
  <div class="watchlist">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        {{ $t('watchlist.title') }}
      </h1>
      <p class="page-subtitle">
        {{ $t('watchlist.subtitle') }}
      </p>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">
          📊
        </div>
        <div class="stat-content">
          <div class="stat-value">
            {{ stats.total }}
          </div>
          <div class="stat-label">
            {{ $t('watchlist.monitoredProducts') }}
          </div>
        </div>
      </div>
      
      <div class="stat-card highlight">
        <div class="stat-icon">
          🚀
        </div>
        <div class="stat-content">
          <div class="stat-value">
            {{ stats.highPerformance }}
          </div>
          <div class="stat-label">
            {{ $t('watchlist.highPerformance') }}
          </div>
        </div>
      </div>
      
      <div class="stat-card alert">
        <div class="stat-icon">
          ⚠️
        </div>
        <div class="stat-content">
          <div class="stat-value">
            {{ stats.needsAttention }}
          </div>
          <div class="stat-label">
            {{ $t('watchlist.needsAttention') }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- 监控商品列表 -->
    <div
      v-if="watchedProducts.length > 0"
      class="watchlist-content"
    >
      <!-- 筛选和排序 -->
      <div class="watchlist-controls">
        <div class="controls-left">
          <select
            v-model="filterBy"
            class="form-select"
          >
            <option value="all">
              {{ $t('watchlist.allProducts') }}
            </option>
            <option value="high-sales">
              {{ $t('watchlist.highSales') }}
            </option>
            <option value="low-competition">
              {{ $t('watchlist.lowCompetition') }}
            </option>
            <option value="price-drop">
              {{ $t('watchlist.priceDecreased') }}
            </option>
          </select>
          
          <select
            v-model="sortBy"
            class="form-select"
          >
            <option value="added">
              {{ $t('watchlist.sortByDateAdded') }}
            </option>
            <option value="sales">
              {{ $t('watchlist.sortBySales') }}
            </option>
            <option value="price">
              {{ $t('watchlist.sortByPrice') }}
            </option>
            <option value="rating">
              {{ $t('watchlist.sortByRating') }}
            </option>
          </select>
        </div>
        
        <div class="controls-right">
          <button 
            class="btn btn-ghost view-toggle"
            @click="toggleView"
          >
            {{ viewMode === 'grid' ? '📋' : '⊞' }}
          </button>
          
          <button 
            class="btn btn-secondary"
            @click="exportWatchlist"
          >
            {{ $t('watchlist.export') }}
          </button>
          
          <button 
            class="btn btn-danger"
            :disabled="watchedProducts.length === 0"
            @click="clearWatchlist"
          >
            {{ $t('watchlist.clearAll') }}
          </button>
        </div>
      </div>
      
      <!-- 商品列表 -->
      <div class="watchlist-products">
        <!-- 网格视图 -->
        <div
          v-if="viewMode === 'grid'"
          class="products-grid"
        >
          <div 
            v-for="product in filteredProducts" 
            :key="product.id"
            class="watch-card"
          >
            <ProductCard
              :product="product"
              :is-watched="true"
              @view-details="viewProductDetails"
              @toggle-watch="removeFromWatch"
            />
            
            <!-- 监控信息 -->
            <div class="watch-info">
              <div class="watch-status">
                <span
                  class="status-indicator"
                  :class="getStatusClass(product)"
                />
                <span class="status-text">{{ getStatusText(product) }}</span>
              </div>
              
              <div class="watch-actions">
                <button 
                  class="btn btn-ghost btn-sm"
                  :disabled="isInCompare(product.id)"
                  @click="addToCompare(product.id)"
                >
                  {{ isInCompare(product.id) ? $t('watchlist.alreadyInCompare') : $t('watchlist.addToCompare') }}
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 列表视图 -->
        <div
          v-else
          class="products-table"
        >
          <DataTable
            title=""
            :columns="tableColumns"
            :data="filteredProducts"
            :empty-text="$t('watchlist.noProducts')"
            @row-click="viewProductDetails"
            @sort-change="handleSort"
          >
            <template #actions="{ item }">
              <div class="table-actions">
                <button 
                  class="btn btn-ghost btn-sm"
                  @click="viewProductDetails(item.id)"
                >
                  {{ $t('common.view') }}
                </button>
                <button 
                  class="btn btn-secondary btn-sm"
                  :disabled="isInCompare(item.id)"
                  @click="addToCompare(item.id)"
                >
                  {{ $t('common.compare') }}
                </button>
                <button 
                  class="btn btn-danger btn-sm"
                  @click="removeFromWatch(item.id)"
                >
                  {{ $t('common.remove') }}
                </button>
              </div>
            </template>
          </DataTable>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div
      v-else
      class="empty-watchlist"
    >
      <div class="empty-icon">
        👁️
      </div>
      <div class="empty-title">
        {{ $t('watchlist.emptyState.title') }}
      </div>
      <div class="empty-text">
        {{ $t('watchlist.emptyState.description') }}
      </div>
      <router-link
        to="/search"
        class="btn btn-primary empty-action-btn"
      >
        <span class="btn-icon">+</span> {{ $t('watchlist.emptyState.actionButton') }}
      </router-link>
    </div>
  </div>
</template>

<script>
/**
 * 监控列表页面组件
 * 管理用户关注的商品列表
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProductStore } from '../stores/useProductStore.js'
import ProductCard from '../components/ProductCard.vue'
import DataTable from '../components/DataTable.vue'

export default {
  name: 'Watchlist',
  
  components: {
    ProductCard,
    DataTable
  },
  
  setup() {
    const router = useRouter()
    const productStore = useProductStore()
    const { t } = useI18n()
    
    // 响应式数据
    const viewMode = ref('grid') // 'grid' | 'list'
    const filterBy = ref('all')
    const sortBy = ref('added')
    
    // 计算属性
    const watchedProducts = computed(() => productStore.watchedProducts)
    
    const stats = computed(() => ({
      total: watchedProducts.value.length,
      highPerformance: watchedProducts.value.filter(product => 
        product.sales > 10000 && product.rating >= 4.5
      ).length,
      needsAttention: watchedProducts.value.filter(product => 
        product.competition === 'high' || product.rating < 4.0
      ).length
    }))
    
    const highPerformanceCount = computed(() => {
      return watchedProducts.value.filter(product => 
        product.sales > 10000 && product.rating >= 4.5
      ).length
    })
    
    const alertCount = computed(() => {
      return watchedProducts.value.filter(product => 
        product.competition === 'high' || product.rating < 4.0
      ).length
    })
    
    const filteredProducts = computed(() => {
      let products = [...watchedProducts.value]
      
      // 筛选
      switch (filterBy.value) {
        case 'high-sales':
          products = products.filter(p => p.sales > 5000)
          break
        case 'low-competition':
          products = products.filter(p => p.competition === 'low')
          break
        case 'price-drop':
          // 模拟价格下降筛选
          products = products.filter(() => Math.random() > 0.7)
          break
      }
      
      // 排序
      switch (sortBy.value) {
        case 'sales':
          products.sort((a, b) => b.sales - a.sales)
          break
        case 'price':
          products.sort((a, b) => a.price - b.price)
          break
        case 'rating':
          products.sort((a, b) => b.rating - a.rating)
          break
        case 'added':
        default:
          // 保持原有顺序（模拟添加时间）
          break
      }
      
      return products
    })
    
    // 表格列定义
    const tableColumns = computed(() => [
      { key: 'title', label: t('watchlist.productName'), sortable: true },
      { key: 'platform', label: t('watchlist.platform'), sortable: true },
      { key: 'price', label: t('watchlist.price'), sortable: true },
      { key: 'sales', label: t('watchlist.sales'), sortable: true },
      { key: 'rating', label: t('watchlist.rating'), sortable: true },
      { key: 'competition', label: t('watchlist.competition'), sortable: true },
      { key: 'actions', label: t('watchlist.actions'), sortable: false }
    ])
    
    // 方法
    const getStatusClass = (product) => {
      if (product.sales > 10000 && product.rating >= 4.5) {
        return 'status-good'
      } else if (product.competition === 'high' || product.rating < 4.0) {
        return 'status-warning'
      }
      return 'status-normal'
    }
    
    const getStatusText = (product) => {
      if (product.sales > 10000 && product.rating >= 4.5) {
        return t('watchlist.status.good')
      } else if (product.competition === 'high') {
        return t('watchlist.status.competitionHigh')
      } else if (product.rating < 4.0) {
        return t('watchlist.status.ratingLow')
      }
      return t('watchlist.status.normal')
    }
    
    const toggleView = () => {
      viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid'
    }
    
    const isInCompare = (productId) => {
      return productStore.isInCompare(productId)
    }
    
    const addToCompare = (productId) => {
      if (!isInCompare(productId)) {
        productStore.addToCompare(productId)
      }
    }
    
    const removeFromWatch = (productId) => {
      productStore.toggleWatch(productId)
    }
    
    const viewProductDetails = (productId) => {
      router.push(`/products/${productId}`)
    }
    
    const handleSort = (column) => {
      sortBy.value = column
    }
    
    const exportWatchlist = () => {
      const data = watchedProducts.value.map(product => ({
        title: product.title,
        platform: product.platform,
        category: product.category,
        price: product.price,
        sales: product.sales,
        rating: product.rating,
        competition: product.competition,
        url: product.url
      }))
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'watchlist.json'
      a.click()
      URL.revokeObjectURL(url)
    }
    
    const clearWatchlist = () => {
      if (confirm(t('watchlist.clearConfirm'))) {
        watchedProducts.value.forEach(product => {
          productStore.toggleWatch(product.id)
        })
      }
    }
    
    // 生命周期钩子
    onMounted(async () => {
      // 确保store已初始化
      if (!productStore.isInitialized) {
        await productStore.initialize()
      }
    })
    
    return {
      viewMode,
      filterBy,
      sortBy,
      watchedProducts,
      stats,
      highPerformanceCount,
      alertCount,
      filteredProducts,
      tableColumns,
      getStatusClass,
      getStatusText,
      toggleView,
      isInCompare,
      addToCompare,
      removeFromWatch,
      viewProductDetails,
      handleSort,
      exportWatchlist,
      clearWatchlist
    }
  }
}
</script>

<style scoped>
.watchlist-page {
  max-width: 1200px;
  margin: 0 auto;
}

/* 页面头部 */
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

/* 统计卡片 */
.watchlist-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 12px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-muted);
}

/* 控制区域 */
.watchlist-controls {
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 16px 20px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.controls-left,
.controls-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-toggle {
  padding: 8px;
  font-size: 16px;
}

/* 商品列表 */
.watchlist-products {
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.watch-card {
  border: 1px solid #f1f5f9;
  border-radius: var(--radius);
  overflow: hidden;
  transition: all 0.2s ease;
}

.watch-card:hover {
  border-color: #e2e8f0;
  box-shadow: var(--shadow);
}

/* 监控信息 */
.watch-info {
  padding: 12px 16px;
  background: #fafbfc;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.watch-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-good {
  background: var(--color-success);
}

.status-warning {
  background: var(--color-warning);
}

.status-normal {
  background: #94a3b8;
}

.status-text {
  font-size: 12px;
  color: var(--color-text-muted);
}

.watch-actions .btn {
  font-size: 12px;
  padding: 4px 8px;
}

/* 表格操作 */
.table-actions {
  display: flex;
  gap: 4px;
}

.table-actions .btn {
  font-size: 12px;
  padding: 4px 8px;
}

/* 空状态 */
.empty-watchlist {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 80px 20px;
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
}

.empty-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 12px;
}

.empty-text {
  font-size: 16px;
  color: var(--color-text-muted);
  margin-bottom: 32px;
  max-width: 450px;
  line-height: 1.6;
}

.empty-action-btn {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  transform: translateY(0);
}

.empty-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.2);
}

.btn-icon {
  font-size: 18px;
  font-weight: 700;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .watchlist-stats {
    grid-template-columns: 1fr;
  }
  
  .watchlist-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .controls-left,
  .controls-right {
    justify-content: space-between;
  }
  
  .products-grid {
    grid-template-columns: 1fr;
  }
  
  .watch-info {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .watch-status {
    justify-content: center;
  }
}
</style>