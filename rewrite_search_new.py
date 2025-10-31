from pathlib import Path
from textwrap import dedent

path = Path('Search.vue')
text = path.read_text(encoding='utf-8')
template, rest = text.split('<script>', 1)
_, style = rest.split('</script>', 1)

new_script = dedent('''\
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ProductCard from '../components/ProductCard.vue'
import DataTable from '../components/DataTable.vue'
import { useProductStore } from '../stores/useProductStore.js'

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
      const unique = new Set(productStore.products.map(product => product.platform))
      return Array.from(unique)
    })

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
        platform: product.platform,
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
        router.push(/products/)
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
      isWatched: productStore.isWatched,
      isInCompare: productStore.isInCompare
    }
  }
}
''')

path.write_text(template + '<script>\n' + new_script + '\n</script>' + style, encoding='utf-8')
