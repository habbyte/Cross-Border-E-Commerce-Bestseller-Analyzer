<template>
  <div class="dashboard">
    <!-- 专属选品策略师模块 - 最顶部 -->
    <div class="strategy-advisor">
      <div class="advisor-header">
        <div class="advisor-icon">🎯</div>
        <h2 class="advisor-title">{{ $t('dashboard.strategyAdvisor.greeting', { name: userName }) }}</h2>
      </div>
      <ul class="advisor-suggestions">
        <li class="suggestion-item">
          <span class="suggestion-icon">📈</span>
          {{ $t('dashboard.strategyAdvisor.suggestions.categoryTrend') }}
        </li>
        <li class="suggestion-item">
          <span class="suggestion-icon">⚠️</span>
          {{ $t('dashboard.strategyAdvisor.suggestions.priceAlert') }}
        </li>
        <li class="suggestion-item">
          <span class="suggestion-icon">💡</span>
          {{ $t('dashboard.strategyAdvisor.suggestions.searchRecommendation') }}
        </li>
      </ul>
    </div>

    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">{{ $t('dashboard.title') }}</h1>
      <p class="page-subtitle">{{ $t('dashboard.subtitle') }}</p>
    </div>
    
    <!-- 第一排：4个核心KPI数据卡片 -->
    <div class="statistics-cards">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📝</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalProducts }}</div>
            <div class="stat-label">{{ $t('dashboard.totalProducts') }}</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">⚖️</div>
          <div class="stat-content">
            <div class="stat-value">{{ compareProducts.length }}</div>
            <div class="stat-label">{{ $t('dashboard.compareList') }}</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">👁️</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.watchedProducts }}</div>
            <div class="stat-label">{{ $t('dashboard.watchedProducts') }}</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">🔥</div>
          <div class="stat-content">
            <div class="stat-value">{{ topProducts.length }}</div>
            <div class="stat-label">{{ $t('dashboard.hotProducts') }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 第二排：3个图表卡片 -->
    <div class="charts-grid">
      <!-- 热度趋势图表 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">{{ $t('dashboard.trendAnalysis.title') }}</h3>
        </div>
        <div class="chart-content">
          <div class="trend-stats">
            <div class="trend-item">
              <span class="trend-label">{{ $t('dashboard.trendAnalysis.weeklyTrend') }}</span>
              <div class="trend-bar">
                <div class="trend-fill trend-up" style="width: 75%"></div>
              </div>
              <span class="trend-value">+15%</span>
            </div>
            <div class="trend-item">
              <span class="trend-label">{{ $t('dashboard.trendAnalysis.lastWeekTrend') }}</span>
              <div class="trend-bar">
                <div class="trend-fill trend-stable" style="width: 60%"></div>
              </div>
              <span class="trend-value">+2%</span>
            </div>
            <div class="trend-item">
              <span class="trend-label">{{ $t('dashboard.trendAnalysis.monthlyTrend') }}</span>
              <div class="trend-bar">
                <div class="trend-fill trend-down" style="width: 45%"></div>
              </div>
              <span class="trend-value">-8%</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 利润率分布图表 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">{{ $t('dashboard.profitDistribution') }}</h3>
        </div>
        <div class="chart-content">
          <div class="profit-stats">
            <div class="profit-item">
              <span class="profit-label">{{ $t('dashboard.highProfit') }}</span>
              <div class="profit-bar">
                <div 
                  class="profit-fill profit-high" 
                  :style="{ width: getProfitPercentage('high') + '%' }"
                ></div>
              </div>
              <span class="profit-count">{{ getProfitCount('high') }}</span>
              <span class="profit-badge profit-high-badge">{{ $t('dashboard.profitBadges.highPotential') }}</span>
            </div>
            <div class="profit-item">
              <span class="profit-label">{{ $t('dashboard.mediumProfit') }}</span>
              <div class="profit-bar">
                <div 
                  class="profit-fill profit-medium" 
                  :style="{ width: getProfitPercentage('medium') + '%' }"
                ></div>
              </div>
              <span class="profit-count">{{ getProfitCount('medium') }}</span>
              <span class="profit-badge profit-medium-badge">{{ $t('dashboard.profitBadges.goodPotential') }}</span>
            </div>
            <div class="profit-item">
              <span class="profit-label">{{ $t('dashboard.lowProfit') }}</span>
              <div class="profit-bar">
                <div 
                  class="profit-fill profit-low" 
                  :style="{ width: getProfitPercentage('low') + '%' }"
                ></div>
              </div>
              <span class="profit-count">{{ getProfitCount('low') }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 竞争度分析图表 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">{{ $t('dashboard.competitionAnalysis') }}</h3>
        </div>
        <div class="chart-content">
          <div class="competition-stats">
            <div class="competition-item">
              <span class="competition-label">{{ $t('dashboard.lowCompetition') }}</span>
              <div class="competition-bar">
                <div 
                  class="competition-fill competition-low" 
                  :style="{ width: getCompetitionPercentage('low') + '%' }"
                ></div>
              </div>
              <span class="competition-count">{{ getCompetitionCount('low') }}</span>
              <span class="competition-badge competition-low-badge">{{ $t('dashboard.competitionBadges.blueOcean') }}</span>
            </div>
            <div class="competition-item">
              <span class="competition-label">{{ $t('dashboard.mediumCompetition') }}</span>
              <div class="competition-bar">
                <div 
                  class="competition-fill competition-medium" 
                  :style="{ width: getCompetitionPercentage('medium') + '%' }"
                ></div>
              </div>
              <span class="competition-count">{{ getCompetitionCount('medium') }}</span>
              <span class="competition-badge competition-medium-badge">{{ $t('dashboard.competitionBadges.competitive') }}</span>
            </div>
            <div class="competition-item">
              <span class="competition-label">{{ $t('dashboard.highCompetition') }}</span>
              <div class="competition-bar">
                <div 
                  class="competition-fill competition-high" 
                  :style="{ width: getCompetitionPercentage('high') + '%' }"
                ></div>
              </div>
              <span class="competition-count">{{ getCompetitionCount('high') }}</span>
              <span class="competition-badge competition-high-badge">{{ $t('dashboard.competitionBadges.redOcean') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 第三排：今日焦点/热门商品列表 -->
    <div class="recent-products">
      <div class="section-header">
        <h3 class="section-title">{{ $t('dashboard.todayFocus') }}</h3>
        <router-link to="/products" class="section-link">{{ $t('dashboard.viewAll') }}</router-link>
      </div>
      <div class="products-grid">
        <ProductCard 
          v-for="product in topProducts.slice(0, 4)" 
          :key="product.id"
          :product="product"
          @view="viewProduct"
          @toggle-watch="toggleWatch"
        />
      </div>
    </div>
    
    <!-- 删除热门商品模块：将来移至商品搜索页面 -->
  </div>
</template>

<script>
/**
 * Dashboard 页面组件
 * 展示核心数据统计和热门商品概览
 */
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProductStore } from '../stores/useProductStore.js'
import ProductCard from '../components/ProductCard.vue'

export default {
  name: 'Dashboard',
  
  components: {
    ProductCard
  },
  
  setup() {
    const router = useRouter()
    const productStore = useProductStore()
    
    // 用户名 - 可以从用户设置或认证状态获取
    const userName = '选品专家'
    
    // 计算属性
    const stats = computed(() => productStore.statistics)
    const topProducts = computed(() => productStore.topProducts)
    const watchedProducts = computed(() => productStore.watchedProducts)
    const compareProducts = computed(() => productStore.compareProducts)
    
    /**
     * 计算平台占比百分比
     * @param {number} count - 平台商品数量
     * @return {number} 百分比值
     */
    const getPlatformPercentage = (count) => {
      const total = stats.value.totalProducts
      return total > 0 ? Math.round((count / total) * 100) : 0
    }
    
    /**
     * 获取特定利润率范围的商品数量
     * @param {string} type - 利润率类型：high/medium/low
     * @return {number} 商品数量
     */
    const getProfitCount = (type) => {
      if (!productStore.products || productStore.products.length === 0) return 0
      
      return productStore.products.filter(product => {
        if (type === 'high') return product.marginRate > 30
        if (type === 'medium') return product.marginRate >= 10 && product.marginRate <= 30
        if (type === 'low') return product.marginRate < 10
        return false
      }).length
    }
    
    /**
     * 计算特定利润率范围的商品占比
     * @param {string} type - 利润率类型：high/medium/low
     * @return {number} 百分比值
     */
    const getProfitPercentage = (type) => {
      const total = stats.value.totalProducts
      const count = getProfitCount(type)
      return total > 0 ? Math.round((count / total) * 100) : 0
    }
    
    /**
     * 获取特定竞争度范围的商品数量
     * @param {string} type - 竞争度类型：low/medium/high
     * @return {number} 商品数量
     */
    const getCompetitionCount = (type) => {
      if (!productStore.products || productStore.products.length === 0) return 0
      
      return productStore.products.filter(product => {
        if (type === 'low') return product.competitionScore < 30
        if (type === 'medium') return product.competitionScore >= 30 && product.competitionScore <= 70
        if (type === 'high') return product.competitionScore > 70
        return false
      }).length
    }
    
    /**
     * 计算特定竞争度范围的商品占比
     * @param {string} type - 竞争度类型：low/medium/high
     * @return {number} 百分比值
     */
    const getCompetitionPercentage = (type) => {
      const total = stats.value.totalProducts
      const count = getCompetitionCount(type)
      return total > 0 ? Math.round((count / total) * 100) : 0
    }
    
    /**
     * 跳转到商品详情页
     * @param {string} productId - 商品ID
     */
    const viewProduct = (productId) => {
      router.push(`/products/${productId}`)
    }
    
    /**
     * 切换商品监控状态
     * @param {string} productId - 商品ID
     */
    const toggleWatch = (productId) => {
      productStore.toggleWatch(productId)
    }
    
    // 生命周期
    onMounted(async () => {
      // 确保数据已加载
      if (!productStore.isInitialized) {
        await productStore.initialize()
      }
    })
    
    return {
      productStore,
      userName,
      stats,
      topProducts,
      watchedProducts,
      compareProducts,
      viewProduct,
      toggleWatch,
      getPlatformPercentage,
      getProfitCount,
      getProfitPercentage,
      getCompetitionCount,
      getCompetitionPercentage
    }
  }
}
</script>

<style scoped>
/* 专属策略师模块样式 */
.strategy-advisor {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 32px;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.advisor-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.advisor-icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.advisor-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.advisor-suggestions {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.suggestion-item:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.suggestion-icon {
  font-size: 18px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* 热度趋势图表样式 */
.trend-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.trend-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trend-label {
  width: 80px;
  font-size: 14px;
  color: var(--color-text);
}

.trend-bar {
  flex: 1;
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.trend-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.trend-up {
  background: #10b981;
}

.trend-stable {
  background: #f59e0b;
}

.trend-down {
  background: #ef4444;
}

.trend-value {
  width: 50px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.dashboard {
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

/* 1. 统计卡片区域 */
.statistics-cards {
  margin-bottom: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
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

.stat-content {
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

/* 2. 图表区域 */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.chart-card {
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
}

.chart-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f3f4f6;
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.chart-content {
  min-height: 200px;
}

/* 平台统计图表 */
.platform-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.platform-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.platform-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.platform-name {
  width: 80px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

.platform-bar {
  flex: 1;
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.platform-fill {
  height: 100%;
  background: var(--color-brand);
  transition: width 0.3s ease;
}

.platform-count {
  width: 40px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

/* 利润率图表 */
.profit-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.profit-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.profit-label {
  width: 120px;
  font-size: 14px;
  color: var(--color-text);
}

.profit-bar {
  flex: 1;
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.profit-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.profit-high {
  background: #10b981;
}

.profit-medium {
  background: #f59e0b;
}

.profit-low {
  background: #ef4444;
}

.profit-count {
  width: 30px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.profit-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 12px;
  font-weight: 500;
}

.profit-high-badge {
  background-color: rgba(249, 115, 22, 0.1);
  color: #f97316;
}

.profit-medium-badge {
  background-color: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

/* 竞争度图表 */
.competition-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.competition-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.competition-label {
  width: 80px;
  font-size: 14px;
  color: var(--color-text);
}

.competition-bar {
  flex: 1;
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.competition-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.competition-low {
  background: #10b981;
}

.competition-medium {
  background: #f59e0b;
}

.competition-high {
  background: #ef4444;
}

.competition-count {
  width: 30px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.competition-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 12px;
  font-weight: 500;
}

.competition-low-badge {
  background-color: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.competition-medium-badge {
  background-color: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.competition-high-badge {
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* 3. 今日焦点产品列表 */
.recent-products {
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f3f4f6;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.section-link {
  color: var(--color-brand);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}

.section-link:hover {
  text-decoration: underline;
}

/* 商品网格 */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  margin-top: 16px;
}

/* 确保在桌面端至少显示3-4个商品卡片 */
@media (min-width: 1200px) {
  .products-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 900px) and (max-width: 1199px) {
  .products-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 600px) and (max-width: 899px) {
  .products-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 599px) {
  .products-grid {
    grid-template-columns: 1fr;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .profit-label {
    width: 100px;
  }
  
  .competition-label {
    width: 70px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .profit-label {
    width: 80px;
    font-size: 12px;
  }
  
  .competition-label {
    width: 60px;
    font-size: 12px;
  }
  
  .products-grid {
    grid-template-columns: 1fr;
  }
}
</style>
