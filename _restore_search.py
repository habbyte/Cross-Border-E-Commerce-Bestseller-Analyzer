from pathlib import Path

path = Path("C:/Users/杨世锋/Desktop/跨境电商爆款分析器/src/views/Search.vue")
text = path.read_text(encoding="utf-8")
start = text.index("<script>")
end = text.index("</script>", start)
new_script = """<script>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProductStore } from '../stores/useProductStore'

export default {
  name: 'Search',
  setup() {
    const router = useRouter()
    const { t } = useI18n()
    const productStore = useProductStore()

    const searchQuery = ref('')
    const currentPage = ref(1)
    const pageSize = ref(12)

    const tableColumns = computed(() => ([
      { key: 'title', label: t('search.table.name') },
      { key: 'platform', label: t('search.table.platform') },
      { key: 'formattedPrice', label: t('search.table.price') },
      { key: 'sales', label: t('search.table.sales') },
      { key: 'rating', label: t('search.table.rating') },
      { key: 'competition', label: t('search.table.competition') },
    ]))

    const filteredProducts = computed(() => {
      const products = productStore.products || []
      const q = searchQuery.value.trim().toLowerCase()
      return products
        .map(p => ({
          ...p,
          sales: Math.floor(Math.random() * 1000) + 100,
          rating: (Math.random() * 2 + 3).toFixed(1),
          competition: Math.random() > 0.66 ? 'high' : (Math.random() > 0.5 ? 'medium' : 'low')
        }))
        .filter(p => !q || p.title.toLowerCase().includes(q))
    })

    const totalPages = computed(() => Math.ceil(filteredProducts.value.length / pageSize.value) || 1)
    const paginatedProducts = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      return filteredProducts.value.slice(start, start + pageSize.value)
    })

    const prevPage = () => {
      if (currentPage.value > 1) currentPage.value -= 1
    }

    const nextPage = () => {
      if (currentPage.value < totalPages.value) currentPage.value += 1
    }

    const viewDetails = (id) => {
      router.push(`/products/${id}`)
    }

    return {
      t,
      searchQuery,
      currentPage,
      pageSize,
      tableColumns,
      filteredProducts,
      totalPages,
      paginatedProducts,
      prevPage,
      nextPage,
      viewDetails,
    }
  }
}
</script>"""
new_text = text[:start] + new_script + text[end + len("</script>"):]
path.write_text(new_text, encoding="utf-8")
