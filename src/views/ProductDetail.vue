<template>
  <div class="product-detail">
    <!-- 页面标题 / Page Header -->
    <div class="page-header">
      <button
        class="btn btn-ghost back-btn"
        @click="goBack"
      >
        {{ $t('productDetail.goBack') }}
      </button>
      <h1 class="page-title">
        📦 {{ $t('productDetail.title') }}
      </h1>
    </div>
    
    <!-- 商品信息展示 / Product Content -->
    <TriState
      :loading="loading"
      :error="detailError"
      :empty="product ? 0 : 1"
      :empty-text="$t('productDetail.notFound')"
    >
      <template #default>
        <div
          v-if="product"
          class="product-content"
        >
          <!-- 商品头部信息 / Header -->
          <div class="product-header">
            <div class="product-image">
              <img 
                v-img-fallback
                :src="product?.imageUrl || placeholderImage" 
                :alt="product?.title || t('common.product')" 
              >
            </div>
        
            <div class="product-info">
              <h2 class="product-title">
                {{ product.title }}
              </h2>
              <div class="product-meta">
                <span class="product-platform">{{ product.platform }}</span>
                <span class="product-category">{{ product.category }}</span>
              </div>
          
              <div class="product-stats">
                <div class="stat-item">
                  <span class="stat-label">{{ $t('productDetail.price') }}</span>
                  <span class="stat-value price">{{ product.formattedPrice }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">{{ $t('productDetail.sales') }}</span>
                  <span class="stat-value">{{ product.sales.toLocaleString() }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">{{ $t('productDetail.rating') }}</span>
                  <span class="stat-value">{{ product.rating }}/5</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">{{ $t('productDetail.competitionLabel') }}</span>
                  <span
                    class="stat-value"
                    :class="`competition-${product.competition}`"
                  >
                    {{ getCompetitionText(product.competition) }}
                  </span>
                </div>
              </div>
          
              <div class="product-actions">
                <button 
                  class="btn btn-primary"
                  @click="toggleWatch"
                >
                  {{ isWatched ? $t('productDetail.removeFromWatchlist') : $t('productDetail.addToWatchlist') }}
                </button>
            
                <button 
                  class="btn btn-secondary"
                  :disabled="isInCompare"
                  @click="addToCompare"
                >
                  {{ isInCompare ? $t('productDetail.removeFromCompare') : $t('productDetail.addToCompare') }}
                </button>
              </div>
            </div>
          </div>
      
          <!-- 详细信息 / Details -->
          <div class="product-details">
            <div class="detail-section">
              <h3 class="detail-title">
                {{ $t('productDetail.description') }}
              </h3>
              <p class="detail-content">
                {{ product.description || $t('productDetail.noDescription') }}
              </p>
            </div>
        
            <div class="detail-section">
              <h3 class="detail-title">
                {{ $t('productDetail.keywords') }}
              </h3>
              <div class="keywords">
                <div 
                  v-for="keyword in (product.tags || [])" 
                  :key="keyword"
                  class="keyword-tag"
                >
                  <span class="keyword-text">{{ keyword }}</span>
                  <button 
                    class="copy-btn" 
                    title="复制关键词"
                    @click="copyToClipboard(keyword)"
                  >
                    📋
                  </button>
                </div>
              </div>
              <div
                v-if="showCopyNotification"
                class="copy-notification"
              >
                复制成功！
              </div>
            </div>
          </div>
        </div>
      </template>
    </TriState>
  </div>
</template>

<script>
/**
 * ProductDetail component / 商品详情组件
 * 负责展示单个商品的详细信息，包含基本信息、统计数据、描述与关键词
 * 函数级注释遵循清晰、简洁的原则，避免过度复杂。
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProductStore } from '@/stores/useProductStore.js'
import TriState from '@/components/common/TriState.vue'

export default {
  name: 'ProductDetail',
  components: { TriState },
  
  props: {
    id: {
      type: String,
      required: true
    }
  },
  
  setup(props) {
    const router = useRouter()
    const productStore = useProductStore()
    const { t } = useI18n()
    
    // 响应式数据 / Reactive state
    const loading = ref(true)
    const detailError = ref('')
    const showCopyNotification = ref(false)
    
    // 商品详情：挂载后初始化再获取，避免首屏未初始化导致的"不存在"
    const product = ref(null)
    
    // 计算属性 / Computed: is product watched
    const isWatched = computed(() => {
      return productStore.isWatched(props.id)
    })
    
    // 计算属性 / Computed: is product in compare list
    const isInCompare = computed(() => {
      return productStore.isInCompare(props.id)
    })
    
    /**
     * placeholderImage
     * 使用国际化文案并 URL 编码，作为商品详情占位图，避免中文字符导致加载错误
     */
    const placeholderImage = computed(() => `https://via.placeholder.com/300x300?text=${encodeURIComponent(t('common.product'))}`)
    
    /**
     * getCompetitionText / 获取竞争程度文案
     * 将内部枚举 level 映射为国际化文案，避免在模板中堆砌条件
     */
    const getCompetitionText = (level) => {
      const texts = {
        low: t('productDetail.competition.low'),
        medium: t('productDetail.competition.medium'),
        high: t('productDetail.competition.high')
      }
      return texts[level] || level
    }
    
    /**
     * toggleWatch / 切换关注状态
     * 简单地委托给 store，保持视图层无业务逻辑
     */
    const toggleWatch = () => {
      productStore.toggleWatch(props.id)
    }
    
    /**
     * addToCompare / 加入对比列表
     * 若未在对比列表，则添加。避免重复添加的特殊情况
     */
    const addToCompare = () => {
      if (!isInCompare.value) {
        productStore.addToCompare(props.id)
      }
    }
    
    /**
     * goBack / 返回上一页
     * 只做一件事：回退历史。不要在此混入额外逻辑。
     */
    const goBack = () => {
      router.go(-1)
    }
    
    /**
     * copyToClipboard / 复制文本到剪贴板
     * @param {string} text - 要复制的文本
     * 复制成功后显示通知，并在短时间后自动隐藏
     */
    const copyToClipboard = (text) => {
      navigator.clipboard.writeText(text)
        .then(() => {
          showCopyNotification.value = true
          setTimeout(() => {
            showCopyNotification.value = false
          }, 2000)
        })
        .catch(err => {
          console.error('复制失败:', err)
        })
    }
    
    /**
     * onMounted / 组件挂载
     * 初始化数据并设置加载状态。保持清晰和可恢复。
     */
    onMounted(async () => {
      try {
        loading.value = true
        detailError.value = ''
        
        // 确保数据已加载 / ensure store initialized
        if (!productStore.isInitialized) {
          await productStore.initialize()
        }

        // 加载指定商品（會自動從 API 獲取如果本地沒有）
        try {
          product.value = await productStore.getProduct(props.id)
        } catch (err) {
          detailError.value = err?.message || 'Failed to load product'
          product.value = null
          console.error('[ProductDetail] Failed to load product:', err)
        }
      } finally {
        loading.value = false
      }
    })
    
    return {
      product,
      loading,
      detailError,
      isWatched,
      isInCompare,
      showCopyNotification,
      placeholderImage,
      getCompetitionText,
      toggleWatch,
      addToCompare,
      goBack,
      copyToClipboard,
      t
    }
  }
}
</script>

<style scoped>
.product-detail {
  max-width: 1000px;
  margin: 0 auto;
}

/* 返回导航 */
.back-nav {
  margin-bottom: 24px;
}

/* 商品头部 */
.product-header {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 32px;
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
  margin-bottom: 24px;
}

.product-image {
  aspect-ratio: 1;
  border-radius: var(--radius);
  overflow: hidden;
  background: #f3f4f6;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.product-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
  line-height: 1.3;
}

.product-meta {
  display: flex;
  gap: 12px;
}

.product-platform,
.product-category {
  padding: 4px 8px;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-muted);
}

/* 统计信息 */
.product-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-muted);
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}

.stat-value.price {
  color: var(--color-brand);
}

.competition-low {
  color: var(--color-success);
}

.competition-medium {
  color: var(--color-warning);
}

.competition-high {
  color: var(--color-danger);
}

/* 操作按钮 */
.product-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
}

/* 详细信息 */
.product-details {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section {
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 16px 0;
}

.product-description {
  font-size: 16px;
  line-height: 1.6;
  color: var(--color-text);
  margin: 0;
}

/* 关键词 */
.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background: #f3f4f6;
  border-radius: 20px;
  font-size: 14px;
  color: var(--color-text);
  margin: 0 8px 8px 0;
  transition: all 0.2s ease;
}

.keyword-tag:hover {
  background: #e5e7eb;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.keyword-text {
  margin-right: 6px;
}

.copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  opacity: 0.6;
  transition: all 0.2s ease;
  padding: 0;
}

.copy-btn:hover {
  opacity: 1;
}

.copy-notification {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #10b981;
  color: white;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  animation: fadeInOut 2s ease;
}

@keyframes fadeInOut {
  0% { opacity: 0; transform: translateY(10px); }
  10% { opacity: 1; transform: translateY(0); }
  90% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(-10px); }
}

/* 状态页面 */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.loading-state .spinner,
.loading-state .loading {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f4f6;
  border-top: 3px solid var(--color-brand);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-text {
  font-size: 16px;
  color: var(--color-text-muted);
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.error-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}

.error-text {
  font-size: 16px;
  color: var(--color-text-muted);
  margin-bottom: 24px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .product-header {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .product-image {
    max-width: 250px;
    margin: 0 auto;
  }
  
  .product-stats {
    grid-template-columns: 1fr;
  }
  
  .product-actions {
    flex-direction: column;
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>