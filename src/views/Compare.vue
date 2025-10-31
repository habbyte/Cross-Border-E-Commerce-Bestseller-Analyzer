<template>
  <div class="compare">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">{{ $t('compare.title') }}</h1>
      <p class="page-subtitle">{{ $t('compare.subtitle') }}</p>
    </div>
    
    <!-- 对比内容 -->
    <div v-if="compareProducts.length > 0" class="compare-content">
      <!-- 操作栏 -->
      <div class="compare-toolbar">
        <div class="toolbar-left">
          <span class="compare-count">{{ $t('compare.selectedCount', { count: compareProducts.length }) }}</span>
        </div>
        <div class="toolbar-right">
          <button class="btn btn-secondary" @click="clearCompare">
            {{ $t('compare.clearAll') }}
          </button>
          <button class="btn btn-primary" @click="exportCompare">
            {{ $t('compare.export') }}
          </button>
        </div>
      </div>
      
      <!-- 对比表格 -->
      <div class="comparison-table">
        <table class="table">
          <thead>
            <tr>
              <th class="metric-column">{{ $t('compare.features') }}</th>
              <th 
                v-for="product in compareProducts" 
                :key="product.id"
                class="product-column"
              >
                <div class="product-header">
                  <img :src="product.imageUrl || `https://via.placeholder.com/200x200?text=${$t('common.product')}`" :alt="product.title" class="product-thumb" />
                  <div class="product-info">
                    <h4 class="product-name">{{ product.title }}</h4>
                    <span class="product-platform">{{ product.platform }}</span>
                  </div>
                  <button 
                    class="btn btn-ghost btn-sm remove-btn"
                    @click="removeFromCompare(product.id)"
                    :title="$t('compare.remove')"
                  >
                    ×
                  </button>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- 基本信息 -->
            <tr>
              <td class="metric-name">{{ $t('compare.category') }}</td>
              <td v-for="product in compareProducts" :key="`category-${product.id}`">
                <span class="category-tag">{{ product.category }}</span>
              </td>
            </tr>
            
            <tr class="compare-row">
              <td class="compare-label">{{ $t('compare.price') }}</td>
              <td 
                v-for="product in compareProducts" 
                :key="`price-${product.id}`"
                class="compare-value price"
              >
                {{ product.formattedPrice }}
              </td>
            </tr>
            
            <tr class="compare-row">
              <td class="compare-label">{{ $t('compare.sales') }}</td>
              <td 
                v-for="product in compareProducts" 
                :key="`sales-${product.id}`"
                class="compare-value"
              >
                {{ Math.floor(Math.random() * 1000) + 100 }}
              </td>
            </tr>
            
            <tr class="compare-row">
              <td class="compare-label">{{ $t('compare.rating') }}</td>
              <td 
                v-for="product in compareProducts" 
                :key="`rating-${product.id}`"
                class="compare-value"
              >
                <div class="rating">
                  <span class="rating-value">{{ (Math.random() * 2 + 3).toFixed(1) }}</span>
                  <span class="rating-stars">
                    {{ '★'.repeat(Math.floor(Math.random() * 2 + 3)) }}{{ '☆'.repeat(5 - Math.floor(Math.random() * 2 + 3)) }}
                  </span>
                </div>
              </td>
            </tr>
            
            <tr class="compare-row">
              <td class="compare-label">{{ $t('compare.competitionLabel') }}</td>
              <td 
                v-for="product in compareProducts" 
                :key="`competition-${product.id}`"
                class="compare-value"
              >
                <span :class="`competition-badge competition-${product.competitionLevel}`">
                  {{ getCompetitionText(product.competitionLevel) }}
                </span>
              </td>
            </tr>
            
            <!-- 操作行 -->
            <tr class="compare-row actions-row">
              <td class="compare-label">{{ $t('compare.actions') }}</td>
              <td 
                v-for="product in compareProducts" 
                :key="`actions-${product.id}`"
                class="compare-value"
              >
                <div class="product-actions">
                  <button 
                    class="btn btn-primary btn-sm"
                    @click="viewDetails(product.id)"
                  >
                    {{ $t('compare.viewDetails') }}
                  </button>
                  <button 
                    class="btn btn-secondary btn-sm"
                    @click="toggleWatch(product.id)"
                  >
                    {{ productStore.isWatched(product.id) ? $t('watchlist.removeFromWatchlist') : $t('watchlist.addToWatchlist') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- 对比分析 -->
      <div class="analysis-section">
        <h2 class="section-title">📊 {{ $t('compare.analysis') }}</h2>
        
        <div class="analysis-grid">
          <!-- 价格分析 -->
          <div class="analysis-card">
            <h3 class="analysis-title">{{ $t('compare.priceAnalysis') }}</h3>
            <div class="analysis-content">
              <div class="price-stats">
                <div class="stat-item">
                  <span class="stat-label">{{ $t('compare.lowestPrice') }}</span>
                  <span class="stat-value">{{ settingsStore.formatCurrency(priceAnalysis.min) }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">{{ $t('compare.highestPrice') }}</span>
                  <span class="stat-value">{{ settingsStore.formatCurrency(priceAnalysis.max) }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">{{ $t('compare.averagePrice') }}</span>
                  <span class="stat-value">{{ settingsStore.formatCurrency(Number(priceAnalysis.avg)) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 销量分析 -->
          <div class="analysis-card">
            <h3 class="analysis-title">{{ $t('compare.salesAnalysis') }}</h3>
            <div class="analysis-content">
              <div class="sales-stats">
                <div class="stat-item">
                  <span class="stat-label">{{ $t('compare.highestSales') }}</span>
                  <span class="stat-value">{{ salesAnalysis.max.toLocaleString() }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">{{ $t('compare.averageSales') }}</span>
                  <span class="stat-value">{{ salesAnalysis.avg.toLocaleString() }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 评分分析 -->
          <div class="analysis-card">
            <h3 class="analysis-title">{{ $t('compare.ratingAnalysis') }}</h3>
            <div class="analysis-content">
              <div class="rating-stats">
                <div class="stat-item">
                  <span class="stat-label">{{ $t('compare.highestRating') }}</span>
                  <span class="stat-value">{{ ratingAnalysis.max }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">{{ $t('compare.averageRating') }}</span>
                  <span class="stat-value">{{ ratingAnalysis.avg }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-else class="empty-state">
      <div class="empty-icon">📊</div>
      <h3 class="empty-title">{{ $t('compare.emptyState.title') }}</h3>
      <p class="empty-description">
        {{ $t('compare.emptyState.description') }}
      </p>
      <button class="btn btn-primary empty-action-btn" @click="goToDashboard">
        <span class="btn-icon">🔍</span> {{ $t('compare.emptyState.cta') }}
      </button>
    </div>
    
    <!-- 对比建议 -->
    <div v-if="compareProducts.length > 0 && compareProducts.length < 4" class="compare-suggestions">
      <h3>{{ $t('compare.suggestions') }}</h3>
      <p>{{ $t('compare.suggestionsDesc') }}</p>
      <div class="suggested-products">
        <ProductCard 
          v-for="product in suggestedProducts" 
          :key="product.id"
          :product="product"
          :is-watched="watchedProducts.some(p => p.id === product.id)"
          :is-in-compare="false"
          @view-details="viewProduct"
          @add-to-compare="addToCompare"
        />
      </div>
    </div>
  </div>
</template>

<script>
/**
 * 商品对比页面组件
 * 提供商品对比功能和分析
 */
import { useProductStore } from '../stores/useProductStore'
import { useSettingsStore } from '../stores/useSettingsStore'

export default {
  name: 'Compare',
  
  setup() {
    /**
     * setup / 组件初始化
     * - 引入商品与设置两个 store
     * - 使用 settingsStore 提供的 formatCurrency 进行货币格式化，避免硬编码符号
     */
    const productStore = useProductStore()
    const settingsStore = useSettingsStore()
    
    return {
      productStore,
      settingsStore
    }
  },
  
  computed: {
    /**
     * 获取对比商品列表
     */
    compareProducts() {
      return this.productStore.compareProducts || []
    },
    
    /**
     * 价格分析
     */
    priceAnalysis() {
      if (this.compareProducts.length === 0) return { min: 0, max: 0, avg: 0 }
      
      const prices = this.compareProducts.map(p => p.price)
      return {
        min: Math.min(...prices),
        max: Math.max(...prices),
        avg: (prices.reduce((a, b) => a + b, 0) / prices.length).toFixed(2)
      }
    },
    
    /**
     * 销量分析
     */
    salesAnalysis() {
      if (this.compareProducts.length === 0) return { max: 0, avg: 0 }
      
      // 使用模拟销量数据
      const sales = this.compareProducts.map(() => Math.floor(Math.random() * 1000) + 100)
      return {
        max: Math.max(...sales),
        avg: Math.floor(sales.reduce((a, b) => a + b, 0) / sales.length)
      }
    },
    
    /**
     * 评分分析
     */
    ratingAnalysis() {
      if (this.compareProducts.length === 0) return { max: 0, avg: 0 }
      
      // 使用模拟评分数据
      const ratings = this.compareProducts.map(() => Math.random() * 2 + 3)
      return {
        max: Math.max(...ratings).toFixed(1),
        avg: (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(1)
      }
    }
  },
  
  async mounted() {
    // 确保store已初始化
    if (!this.productStore.isInitialized) {
      await this.productStore.initialize()
    }
  },

  methods: {
    /**
     * 获取竞争程度文本
     */
    getCompetitionText(level) {
      const levels = {
        low: this.$t('compare.competition.low'),
        medium: this.$t('compare.competition.medium'),
        high: this.$t('compare.competition.high')
      }
      return levels[level] || level
    },
    
    /**
     * 查看商品详情
     */
    viewDetails(productId) {
      this.$router.push(`/products/${productId}`)
    },
    
    /**
     * 切换监控状态
     */
    toggleWatch(productId) {
      this.productStore.toggleWatch(productId)
    },
    
    /**
     * 从对比中移除商品
     */
    removeFromCompare(productId) {
      this.productStore.removeFromCompare(productId)
    },
    
    /**
     * 清空对比列表
     */
    clearCompare() {
      this.productStore.clearCompare()
    },
    
    /**
     * 导出对比数据
     */
    exportCompare() {
      alert(this.$t('common.developmentInProgress'))
    },
    
    /**
     * 跳转到搜索页面
     */
    goToSearch() {
      this.$router.push('/search')
    },
    
    /**
     * 跳转到Dashboard页面
     */
    goToDashboard() {
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.compare {
  padding: 24px;
}

.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  color: var(--text-secondary);
  margin: 0;
}

.compare-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.compare-count {
  font-weight: 600;
  color: var(--text-primary);
}

.toolbar-right {
  display: flex;
  gap: 12px;
}

.comparison-table {
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  margin-bottom: 32px;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.table th {
  background: var(--bg-secondary);
  font-weight: 600;
  color: var(--text-primary);
}

.metric-column {
  width: 150px;
  font-weight: 600;
}

.product-column {
  min-width: 200px;
}

.product-header {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.product-thumb {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  object-fit: cover;
}

.product-info {
  flex: 1;
}

.product-name {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--text-primary);
}

.product-platform {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  line-height: 1;
}

.metric-name,
.compare-label {
  font-weight: 600;
  color: var(--text-primary);
}

.category-tag {
  padding: 4px 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.compare-value.price {
  font-weight: 700;
  color: var(--primary-color);
  font-size: 1.1rem;
}

.rating {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rating-value {
  font-weight: 600;
}

.rating-stars {
  color: #fbbf24;
}

.competition-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.competition-low {
  background: #dcfce7;
  color: #166534;
}

.competition-medium {
  background: #fef3c7;
  color: #92400e;
}

.competition-high {
  background: #fee2e2;
  color: #991b1b;
}

.product-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.analysis-section {
  margin-top: 32px;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 24px 0;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
}

.analysis-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-color);
}

.analysis-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.price-stats,
.sales-stats,
.rating-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.stat-value {
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 2px 10px rgba(59, 130, 246, 0.3);
}

.empty-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 12px 0;
}

.empty-description {
  font-size: 16px;
  color: var(--color-text-muted);
  margin: 0 0 32px 0;
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
}

@media (max-width: 768px) {
  .compare-toolbar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .toolbar-right {
    justify-content: center;
  }
  
  .table {
    font-size: 0.875rem;
  }
  
  .table th,
  .table td {
    padding: 12px 8px;
  }
  
  .product-header {
    flex-direction: column;
    text-align: center;
  }
  
  .product-actions {
    justify-content: center;
  }
  
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}
</style>
