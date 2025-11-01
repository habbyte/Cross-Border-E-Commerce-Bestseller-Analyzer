<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProductStore } from '@/stores/useProductStore.js'
import { events } from '@/analytics/events.js'
import { FLAGS as featureFlags } from '@/features/flags.js'

import TriState from '@/components/common/TriState.vue'
import OnboardingSteps from '@/components/onboarding/OnboardingSteps.vue'
import EmptyWarmCard from '@/components/empty/EmptyWarmCard.vue'
import ReasonCard from '@/components/recommendation/ReasonCard.vue'

const router = useRouter()
const store = useProductStore()

const searchQuery = ref('')
const platform = ref('all')

const filteredProducts = computed(() => {
  const filterOptions = { platform: platform.value === 'all' ? '' : platform.value }
  if (typeof store.searchProducts === 'function') {
    return store.searchProducts(searchQuery.value, filterOptions) ?? []
  }
  return store.products ?? []
})

const isEmpty = computed(() => (filteredProducts.value?.length ?? 0) === 0)

const showEmptyWarmCard = computed(
  () =>
    featureFlags.emptyWarmCard &&
    !store.loading &&
    !store.error &&
    isEmpty.value
)

const platformOptions = [
  { value: 'all', labelKey: 'products.filter.all' },
  { value: 'amazon', labelKey: 'settings.platforms.amazon' },
  { value: 'shopee', labelKey: 'settings.platforms.shopee' },
  { value: 'lazada', labelKey: 'settings.platforms.lazada' },
  { value: 'ebay', labelKey: 'settings.platforms.ebay' },
  { value: 'aliexpress', labelKey: 'settings.platforms.aliexpress' }
]

function handleSearchInput() {
  events.track('search_input', { area: 'products', q: searchQuery.value })
}

function handlePlatformChange() {
  events.track('filter_change', { area: 'products', platform: platform.value })
}

function handleLoadSamples() {
  if (typeof store.loadSampleProducts === 'function') {
    store.loadSampleProducts()
    events.track('ui_click', { area: 'products_empty', action: 'load_samples' })
  }
}

function handleViewGuide() {
  console.info('[guide] open usage guide placeholder')
  events.track('ui_click', { area: 'products_empty', action: 'view_guide' })
}

function handleReasonDetails(product) {
  console.info('[reason] details for', product?.id)
  events.track('recommendation_reason_click_detail', { productId: product?.id })
}

function handleToggleWatch(product) {
  if (!product?.id || typeof store.toggleWatch !== 'function') return
  store.toggleWatch(product.id)
  events.track('ui_click', {
    area: 'products_card',
    action: 'toggle_watch',
    productId: product.id,
    watched: store.isWatched?.(product.id) ?? false
  })
}

function handleAddToCompare(product) {
  if (!product?.id) return
  if (typeof store.isInCompare === 'function' && store.isInCompare(product.id)) {
    return
  }
  if (typeof store.addToCompare === 'function') {
    try {
      store.addToCompare(product.id)
      events.track('ui_click', {
        area: 'products_card',
        action: 'add_compare',
        productId: product.id
      })
    } catch (error) {
      console.warn('[compare] failed to add product', product.id, error)
    }
  }
}

function handleViewProduct(product) {
  if (!product?.id) return
  events.track('ui_click', {
    area: 'products_card',
    action: 'view_detail',
    productId: product.id
  })
  router.push({ name: 'ProductDetail', params: { id: product.id } })
}

onMounted(async () => {
  if (typeof store.initialize === 'function') {
    await store.initialize()
  }
  events.track('page_view', { page: 'products' })
})
</script>

<template>
  <section class="page products">
    <header class="page__header">
      <div class="page__heading">
        <h1>{{ $t('products.title') || '商品管理' }}</h1>
        <p class="page__subtitle text-muted">
          {{ $t('products.subtitle') }}
        </p>
      </div>
      <OnboardingSteps
        v-if="featureFlags.onboarding"
        class="page__onboarding"
      />
    </header>

    <div class="toolbar mt-3">
      <label class="sr-only" for="products-search">{{ $t('products.search.placeholder') }}</label>
      <input
        id="products-search"
        v-model="searchQuery"
        class="input"
        type="search"
        :placeholder="$t('products.search.placeholder') || '搜索商品'"
        @input="handleSearchInput"
        aria-label="搜索商品"
      />
      <label class="sr-only" for="products-platform">{{ $t('products.filter.all') }}</label>
      <select
        id="products-platform"
        v-model="platform"
        class="select ml-2"
        @change="handlePlatformChange"
        aria-label="选择平台"
      >
        <option
          v-for="option in platformOptions"
          :key="option.value"
          :value="option.value"
        >
          {{ $t(option.labelKey) }}
        </option>
      </select>
    </div>

    <TriState
      class="mt-4"
      :loading="store.loading"
      :error="store.error || ''"
      :empty="isEmpty"
      :empty-text="$t('products.empty') || ''"
    >
      <template #empty>
        <EmptyWarmCard
          v-if="showEmptyWarmCard"
          @load-sample="handleLoadSamples"
          @view-guide="handleViewGuide"
        />
        <div v-else class="empty-state">
          {{ $t('products.empty') || '暂无数据' }}
        </div>
      </template>

      <template #default>
        <div class="products-grid">
          <article
            v-for="product in filteredProducts"
            :key="product.id"
            class="product-card"
            role="article"
            aria-label="product"
          >
            <header class="product-card__header">
              <div>
                <h3 class="product-card__title">
                  {{ product.name }}
                </h3>
                <p class="product-card__subtitle text-muted">
                  {{ $t(`settings.platforms.${product.platform}`) || product.platform }}
                </p>
              </div>
              <span class="product-card__status">
                {{ $t(`products.status.${product.status}`) || product.status }}
              </span>
            </header>

          <div class="product-card__body">
              <figure class="product-card__media">
                <img
                  v-if="product.imageUrl"
                  :src="product.imageUrl"
                  alt=""
                  class="product-card__image"
                  loading="lazy"
                />
                <div v-else class="product-card__placeholder">
                  <span aria-hidden="true">📦</span>
                </div>
              </figure>
              <dl class="product-card__meta">
                <div class="meta-item">
                  <dt>{{ $t('products.price') }}</dt>
                  <dd>{{ product.formattedPrice ?? product.price }}</dd>
                </div>
                <div class="meta-item">
                  <dt>{{ $t('products.profitMargin') }}</dt>
                  <dd>{{ product.marginRate ?? '--' }}%</dd>
                </div>
                <div class="meta-item">
                  <dt>{{ $t('products.stock') }}</dt>
                  <dd>{{ product.stock ?? 0 }}</dd>
                </div>
                <div class="meta-item">
                  <dt>{{ $t('compare.competitionLabel') }}</dt>
                  <dd>{{ product.competitionScore ?? '--' }}</dd>
                </div>
              </dl>

              <ul v-if="product.tags?.length" class="product-card__tags">
                <li v-for="tag in product.tags" :key="tag">
                  {{ tag }}
                </li>
              </ul>
            </div>

            <footer class="product-card__footer">
              <div class="product-card__actions">
                <button
                  type="button"
                  class="btn btn-secondary"
                  @click="handleToggleWatch(product)"
                >
                  {{
                    store.isWatched?.(product.id)
                      ? $t('watchlist.removeFromWatchlist')
                      : $t('watchlist.addToWatchlist')
                  }}
                </button>
                <button
                  type="button"
                  class="btn btn-secondary"
                  :disabled="store.isInCompare?.(product.id)"
                  @click="handleAddToCompare(product)"
                >
                  {{
                    store.isInCompare?.(product.id)
                      ? $t('products.actions.compared')
                      : $t('products.actions.compare')
                  }}
                </button>
                <button
                  type="button"
                  class="btn btn-primary"
                  @click="handleViewProduct(product)"
                >
                  {{ $t('products.actions.analyze') }}
                </button>
              </div>
              <ReasonCard
                v-if="featureFlags.reasonCard"
                :product="product"
                class="product-card__reason mt-2"
                @view-details="() => handleReasonDetails(product)"
              />
            </footer>
          </article>
        </div>
      </template>
    </TriState>
  </section>
</template>

<style scoped>
.page {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page__header {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.page__heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page__subtitle {
  margin: 0;
  font-size: 0.9rem;
}

.page__onboarding {
  margin-top: 8px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.input,
.select {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #d1d5db);
}

.select {
  min-width: 160px;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.product-card {
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--bg-card, #fff);
}

.product-card__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.product-card__title {
  margin: 0;
  font-size: 1.1rem;
  color: var(--text-primary, #0f172a);
}

.product-card__subtitle {
  margin: 0;
}

.product-card__status {
  font-size: 0.85rem;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.08);
  color: rgba(37, 99, 235, 1);
}

.product-card__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.product-card__media {
  margin: 0;
}

.product-card__image {
  width: 100%;
  border-radius: 8px;
  object-fit: cover;
}

.product-card__placeholder {
  width: 100%;
  height: 140px;
  border-radius: 8px;
  background: rgba(148, 163, 184, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
}

.product-card__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
  margin: 0;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-item dt {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-secondary, #64748b);
}

.meta-item dd {
  margin: 0;
  font-weight: 600;
  color: var(--text-primary, #0f172a);
}

.product-card__tags {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.product-card__tags li {
  background: rgba(59, 130, 246, 0.08);
  color: rgba(37, 99, 235, 1);
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
}

.product-card__footer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.product-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.btn {
  border: none;
  border-radius: 999px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
}

.btn-primary {
  background: var(--primary-color, #2563eb);
  color: #fff;
}

.btn-secondary {
  background: var(--bg-secondary, #f8fafc);
  color: var(--text-primary, #0f172a);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.empty-state {
  padding: 32px;
  text-align: center;
  color: var(--text-secondary, #64748b);
}

.text-muted {
  color: var(--text-secondary, #64748b);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
